import json
import asyncio
from openai import OpenAI
from config import settings

INTENT_SYSTEM_PROMPT = """Jesteś asystentem administratora nieruchomości.
Otrzymujesz transkrypcję dyktowanej notatki lub decyzji.
Wyciągnij intencję i zwróć TYLKO poprawny JSON:

{
  "intent": "create_ticket|add_note|escalate|resolve|call_vendor|schedule|dismiss|unknown",
  "confidence": 0.0,
  "summary": "jedno zdanie — co administrator chce zrobić",
  "entities": {
    "building": "np. budynek B, klatka 3 — lub null",
    "apartment": "np. 4B — lub null",
    "vendor_type": "np. hydraulik, elektryk — lub null",
    "urgency": "natychmiast|dziś|ten_tydzień|null",
    "person": "imię lub nazwisko jeśli wymienione — lub null"
  },
  "suggested_ticket": {
    "category": "maintenance|security|billing|vendor|other",
    "priority": "critical|high|medium|low",
    "body": "treść notatki lub zgłoszenia gotowa do zapisania"
  },
  "human_readable": "Co zrozumiałem: [opis akcji po polsku, 1 zdanie]"
}

Jeśli podano kontekst aktywnego zgłoszenia, słowa takie jak 'to', 'tę sprawę', 'eskaluj', 'zamknij', 'rozwiąż' odnoszą się do tego zgłoszenia.

Przykłady:
- "wezwij hydraulika do budynku B" → intent: call_vendor, vendor_type: hydraulik, building: B
- "eskaluj sprawę bramy, to już tydzień" → intent: escalate
- "rozwiąż tę sprawę" → intent: resolve
- "dodaj notatkę że dzwoniłem do hydraulika" → intent: add_note
- "zadzwoń do Kowalskiego z mieszkania 3A" → intent: call_vendor (person: Kowalski), apartment: 3A
- "odwołaj zlecenie dla elektryka" → intent: dismiss"""


def _interpret_sync(transcript: str, context: str | None) -> dict:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    user_msg = f'Transkrypcja: "{transcript}"'
    if context:
        user_msg += f"\n\nKontekst:\n{context}"
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=512,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": INTENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
    )
    return json.loads(response.choices[0].message.content)


async def interpret_voice_command(transcript: str, context: str | None = None) -> dict:
    return await asyncio.to_thread(_interpret_sync, transcript, context)
