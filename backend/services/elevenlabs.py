import httpx
from config import settings

# ── Intro text builder ──────────────────────────────────────────────────────

def build_intro_text(date_str: str, ticket_count: int, critical_count: int) -> str:
    from services.pl_utils import pl_tickets, pl_critical

    if critical_count == 0:
        urgency = "Brak zgłoszeń krytycznych."
    elif critical_count == 1:
        urgency = "Jedno zgłoszenie krytyczne wymaga natychmiastowej uwagi."
    else:
        critical_str = pl_critical(critical_count)
        urgency = f"{critical_str[0].upper() + critical_str[1:]} wymaga natychmiastowej reakcji."

    return f"Dzień dobry. {date_str}. Masz dziś {pl_tickets(ticket_count)}. {urgency}"

_cached_voice_id: str | None = None


def _is_placeholder(value: str) -> bool:
    return not value or len(value) < 4 or set(value).issubset(set(".-_ "))


async def _resolve_voice_id(api_key: str) -> str:
    global _cached_voice_id
    configured = settings.ELEVENLABS_VOICE_ID

    if not _is_placeholder(configured):
        return configured

    if _cached_voice_id:
        return _cached_voice_id

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": api_key},
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Could not list ElevenLabs voices: {resp.status_code}")
        voices = resp.json().get("voices", [])
        if not voices:
            raise RuntimeError("No voices available in your ElevenLabs account")
        _cached_voice_id = voices[0]["voice_id"]
        return _cached_voice_id


async def synthesize_speech(text: str) -> bytes:
    api_key = settings.ELEVENLABS_API_KEY
    if _is_placeholder(api_key):
        raise RuntimeError("ELEVENLABS_API_KEY not configured in .env")

    voice_id = await _resolve_voice_id(api_key)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": api_key, "Content-Type": "application/json"},
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "style": 0.2},
            },
        )

    if response.status_code != 200:
        raise RuntimeError(f"ElevenLabs {response.status_code}: {response.text[:300]}")

    return response.content
