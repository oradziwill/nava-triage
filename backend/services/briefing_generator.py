"""
Background task: regenerates the voice briefing cache.
Called after every ticket create/update. Never blocks the caller.
"""
import asyncio
import json
import logging
from datetime import datetime

from openai import OpenAI
from sqlalchemy import select

from config import settings
from database import AsyncSessionLocal
from models.ticket import Ticket
from services.briefing_cache import get_cache
from services.elevenlabs import synthesize_speech
from services.pl_utils import polish_date_spoken, pl_tickets

logger = logging.getLogger(__name__)

_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

BRIEFING_SYSTEM = """Napisz tekst do odczytania przez lektora — poranny briefing dla administratora nieruchomości.
Dzisiaj jest {weekday}, {day_ordinal} {month}.
Aktywne zgłoszenia ({ticket_count_word}): {tickets_json}

Zasady dotyczące języka (KRYTYCZNE — lektor czyta tekst wprost):
- Wszystkie liczby pisz SŁOWNIE po polsku: "pięć", "dwanaście", nie "5" ani "12"
- Daty i godziny pisz słownie: "siódmego maja" nie "07.05", "o osiemnastej" nie "18:00"
- Skróty rozwijaj: "budynek B" zostawiasz, ale "ul." → "ulicy", "nr" → "numer"
- Żadnych punktorów, myślników jako list, nawiasów, gwiazdek, znaków specjalnych
- Tylko zdania oddzielone kropkami — tekst musi brzmieć naturalnie czytany na głos

Zasady treści:
- NIE zaczynaj od "Dzień dobry" ani daty — intro zostało już odtworzone
- Zacznij bezpośrednio: "Masz {ticket_count_word} aktywnych spraw."
- Zgłoszenia krytyczne i wysokie: każde w osobnym zdaniu z krótkim opisem problemu i sugerowaną akcją
- Zgłoszenia średnie i niskie: łącznie w jednym zdaniu ("Poza tym trzy sprawy rutynowe...")
- Zakończ jednym konkretnym zaleceniem co zrobić najpierw
- Ton: spokojny, rzeczowy, profesjonalny
- Długość: maksymalnie czterdzieści sekund mówionego tekstu, około sto słów"""


def _build_script_sync(tickets_json: str, weekday: str, day_ordinal: str, month: str, ticket_count_word: str) -> str:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    prompt = BRIEFING_SYSTEM.format(
        weekday=weekday,
        day_ordinal=day_ordinal,
        month=month,
        tickets_json=tickets_json,
        ticket_count_word=ticket_count_word,
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=350,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


async def regenerate_briefing_background() -> None:
    cache = get_cache()
    if cache.is_generating:
        return

    cache.is_generating = True
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Ticket).where(Ticket.status.notin_(["resolved", "dismissed"]))
            )
            tickets = result.scalars().all()

        active = sorted(tickets, key=lambda t: _PRIORITY_ORDER.get(t.priority, 99))[:5]

        if not active:
            script = "Masz dziś zero aktywnych zgłoszeń. Wszystko pod kontrolą."
        else:
            weekday, day_ordinal, month = polish_date_spoken()
            ticket_count_word = pl_tickets(len(tickets))
            payload = json.dumps(
                [
                    {
                        "priority": t.priority,
                        "category": t.category,
                        "summary": t.ai_summary or t.subject or (t.body_raw or "")[:80],
                        "action": t.ai_suggested_action,
                    }
                    for t in active
                ],
                ensure_ascii=False,
            )
            script = await asyncio.to_thread(
                _build_script_sync, payload, weekday, day_ordinal, month, ticket_count_word
            )

        audio = await synthesize_speech(script)

        cache.audio_bytes = audio
        cache.script_text = script
        cache.ticket_count = len(tickets)
        cache.generated_at = datetime.now()
        logger.info("Briefing cache regenerated (%d tickets, %d bytes)", len(tickets), len(audio))

    except Exception:
        logger.exception("Briefing regeneration failed")
    finally:
        cache.is_generating = False


async def warmup_on_startup() -> None:
    await asyncio.sleep(2)
    await regenerate_briefing_background()
