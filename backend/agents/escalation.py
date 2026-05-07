from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.ticket import Ticket

PRIORITY_UP = {"low": "medium", "medium": "high", "high": "critical", "critical": "critical"}


async def run_escalation_check(db: AsyncSession):
    stmt = select(Ticket).where(
        Ticket.follow_up_count >= 2,
        Ticket.status != "resolved",
        Ticket.escalated == False,  # noqa: E712
    )
    result = await db.execute(stmt)
    tickets = result.scalars().all()

    for ticket in tickets:
        new_priority = PRIORITY_UP.get(ticket.priority, ticket.priority)
        ticket.priority = new_priority
        ticket.escalated = True
        note = f"Auto-escalated: {ticket.follow_up_count + 1} follow-ups detected"
        ticket.admin_notes = (ticket.admin_notes or "") + f"\n[SYSTEM] {note}"

    if tickets:
        await db.commit()

    return len(tickets)
