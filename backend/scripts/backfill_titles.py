"""One-time script: generate ai_title for tickets that have none."""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from database import AsyncSessionLocal, init_db
from models.ticket import Ticket
from services.ai_clients import openai_client


async def generate_title(summary: str, subject: str | None) -> str:
    client = openai_client()
    text = subject or summary
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=32,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Zwróć TYLKO JSON: {\"title\": \"...\"}. "
                    "Podaj 2-4 słowa po polsku — krótką rzeczownikową nazwę problemu, "
                    "np. 'zalana piwnica', 'awaria windy', 'brak ogrzewania'. "
                    "Bez cudzysłowów w tytule, bez kropki na końcu."
                ),
            },
            {"role": "user", "content": text},
        ],
    )
    return json.loads(response.choices[0].message.content).get("title", text[:40])


async def main() -> None:
    await init_db()
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Ticket).where(Ticket.ai_title.is_(None)))
        tickets = result.scalars().all()

        if not tickets:
            print("Brak zgłoszeń bez tytułu.")
            return

        print(f"Generuję tytuły dla {len(tickets)} zgłoszeń...")
        for ticket in tickets:
            try:
                title = await generate_title(ticket.ai_summary or ticket.body_raw or "", ticket.subject)
                ticket.ai_title = title
                await db.commit()
                print(f"  #{ticket.id}: {title}")
            except Exception as e:
                print(f"  #{ticket.id}: błąd — {e}")

        print("Gotowe.")


if __name__ == "__main__":
    asyncio.run(main())
