"""Load demo tickets directly into DB (bypasses AI triage for speed)."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from models.ticket import Ticket
from database import Base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://nava:nava_dev@localhost:5432/nava"
)

DEMO_TICKETS = [
    {
        "source": "email",
        "sender_name": "Jan Kowalski",
        "sender_email": "jan.kowalski@gmail.com",
        "sender_type": "resident",
        "subject": "PILNE: Zalanie w piwnicy!",
        "body_raw": "Dzień dobry, w piwnicy budynku B stoi woda od rana. Proszę o natychmiastową pomoc.",
        "priority": "critical",
        "category": "maintenance",
        "status": "new",
        "ai_summary": "Zalanie piwnicy w budynku B — pilna interwencja wymagana.",
        "ai_suggested_action": "Zadzwoń do hydraulika i jedź na miejsce.",
        "ai_reasoning": "Zalanie budynku kwalifikuje się jako sytuacja krytyczna wymagająca natychmiastowej reakcji.",
        "ai_draft_reply": "Dzień dobry Panie Janie,\n\nDziękujemy za szybkie zgłoszenie. Natychmiast wysyłamy ekipę do piwnicy budynku B. Skontaktujemy się z Panem w ciągu 30 minut.\n\nZ poważaniem,\nZarządzanie Nieruchomościami",
    },
    {
        "source": "email",
        "sender_name": "Hydraulik Nowak Sp. z o.o.",
        "sender_email": "faktury@hydraulik-nowak.pl",
        "sender_type": "vendor",
        "subject": "Faktura FV/2024/847",
        "body_raw": "W załączeniu faktura za naprawę instalacji wodnej z dnia 15.01. Proszę o potwierdzenie odbioru.",
        "priority": "medium",
        "category": "vendor",
        "status": "new",
        "ai_summary": "Faktura od dostawcy za naprawę instalacji wodnej — wymaga weryfikacji i akceptacji.",
        "ai_suggested_action": "Sprawdź fakturę FV/2024/847 w systemie księgowym.",
        "ai_reasoning": "Faktura od dostawcy — standardowy priorytet, brak pilności.",
        "ai_draft_reply": "Dzień dobry,\n\nPotwierdzamy odbiór faktury FV/2024/847. Zostanie ona przetworzona w ciągu 7 dni roboczych.\n\nZ poważaniem",
    },
    {
        "source": "email",
        "sender_name": "Maria Wiśniewska",
        "sender_email": "m.wisniewska@wp.pl",
        "sender_type": "resident",
        "subject": "Hałas od sąsiadów",
        "body_raw": "To już trzecia wiadomość w tej sprawie. Mieszkańcy z 4B nadal hałasują po 22. Proszę o interwencję.",
        "priority": "high",
        "category": "complaint",
        "status": "new",
        "follow_up_count": 2,
        "escalated": True,
        "ai_summary": "Powtarzająca się skarga na hałas od mieszkańców 4B po godz. 22 — trzecia wiadomość w sprawie.",
        "ai_suggested_action": "Zadzwoń do mieszkańców z 4B i wyślij oficjalne ostrzeżenie.",
        "ai_reasoning": "Trzecia skarga na ten sam problem — eskalacja do wysokiego priorytetu.",
        "ai_draft_reply": "Dzień dobry Pani Mario,\n\nPrzepraszamy za niedogodności. Podejmujemy natychmiastowe kroki wobec mieszkańców z 4B. Skontaktujemy się z Panią do końca dnia.\n\nZ poważaniem",
        "admin_notes": "\n[SYSTEM] Auto-escalated: 3 follow-ups detected",
    },
    {
        "source": "manual",
        "sender_name": "Zarząd Wspólnoty",
        "sender_type": "board",
        "subject": "Zebranie roczne — agenda",
        "body_raw": "Proszę o przygotowanie sprawozdania finansowego na zebranie w przyszłym tygodniu.",
        "priority": "medium",
        "category": "inquiry",
        "status": "in_progress",
        "ai_summary": "Prośba zarządu o przygotowanie sprawozdania finansowego na zebranie roczne.",
        "ai_suggested_action": "Przygotuj sprawozdanie finansowe do końca tygodnia.",
        "ai_reasoning": "Standardowe żądanie zarządu — ważne, ale niepalące.",
        "ai_draft_reply": "Dzień dobry,\n\nPrzygotujemy sprawozdanie finansowe na wskazany termin. Będzie gotowe do piątku.\n\nZ poważaniem",
    },
    {
        "source": "email",
        "sender_name": "Piotr Dąbrowski",
        "sender_type": "resident",
        "subject": "Brak ogrzewania w mieszkaniu",
        "body_raw": "Od wczoraj nie ma ogrzewania w mieszkaniu 3A. Temperatura spada, proszę o pilną pomoc.",
        "priority": "high",
        "category": "maintenance",
        "status": "new",
        "ai_summary": "Brak ogrzewania w mieszkaniu 3A od wczoraj — pilna naprawa wymagana.",
        "ai_suggested_action": "Wyślij technika do mieszkania 3A jak najszybciej.",
        "ai_reasoning": "Brak ogrzewania w mieszkaniu kwalifikuje się jako wysoki priorytet — komfort i bezpieczeństwo lokatora.",
        "ai_draft_reply": "Dzień dobry Panie Piotrze,\n\nDziękujemy za zgłoszenie. Wysyłamy technika do mieszkania 3A — wizyta planowana na dziś do 16:00. Skontaktujemy się z Panem telefonicznie.\n\nZ poważaniem",
    },
]


async def seed():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        for data in DEMO_TICKETS:
            ticket = Ticket(**data)
            session.add(ticket)
        await session.commit()

    print(f"✓ Inserted {len(DEMO_TICKETS)} demo tickets.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
