from collections.abc import Iterable

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from models.ticket import Ticket

INACTIVE_TICKET_STATUSES = ("resolved", "dismissed")


def append_note(existing_notes: str | None, note: str) -> str:
    if not existing_notes:
        return note
    return f"{existing_notes}\n{note}".strip()


def is_active_ticket_status(status: str) -> bool:
    return status not in INACTIVE_TICKET_STATUSES


def active_tickets(tickets: Iterable[Ticket]) -> list[Ticket]:
    return [ticket for ticket in tickets if is_active_ticket_status(ticket.status)]


async def get_ticket_or_404(db: AsyncSession, ticket_id: int) -> Ticket:
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


async def commit_and_refresh(db: AsyncSession, ticket: Ticket) -> None:
    await db.commit()
    await db.refresh(ticket)
