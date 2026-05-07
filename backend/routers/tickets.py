from fastapi import APIRouter, BackgroundTasks, Depends, Query
from pydantic import BaseModel, ConfigDict, computed_field
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime

from database import get_db
from models.ticket import Ticket
from services.briefing_generator import regenerate_briefing_background
from services.ticket_ops import commit_and_refresh, get_ticket_or_404

router = APIRouter(prefix="/api/tickets", tags=["tickets"])

_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    channel: str
    sender: Optional[str]
    sender_type: str
    subject: Optional[str]
    body_raw: Optional[str]
    priority: str
    category: str
    status: str
    ai_summary: Optional[str]
    ai_draft_reply: Optional[str]
    ai_reasoning: Optional[str]
    ai_suggested_action: Optional[str]
    ai_missing_info: Optional[list] = None
    ai_follow_up_signals: Optional[list] = None
    confidence: Optional[float] = None
    admin_override_priority: Optional[str]
    admin_notes: Optional[str]
    follow_up_count: int
    escalated: bool

    @computed_field
    @property
    def priority_order(self) -> int:
        effective = self.admin_override_priority or self.priority
        return _PRIORITY_ORDER.get(effective, 99)


class TicketPatch(BaseModel):
    status: Optional[str] = None
    admin_notes: Optional[str] = None
    admin_override_priority: Optional[str] = None
    ai_draft_reply: Optional[str] = None


@router.get("", response_model=List[TicketOut])
async def list_tickets(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Ticket)
    if status:
        stmt = stmt.where(Ticket.status == status)
    if priority:
        stmt = stmt.where(Ticket.priority == priority)
    if category:
        stmt = stmt.where(Ticket.category == category)

    result = await db.execute(stmt.order_by(desc(Ticket.created_at)))
    tickets = result.scalars().all()

    return sorted(
        tickets,
        key=lambda t: (_PRIORITY_ORDER.get(t.admin_override_priority or t.priority, 99), -t.created_at.timestamp()),
    )


@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(ticket_id: int, db: AsyncSession = Depends(get_db)):
    return await get_ticket_or_404(db, ticket_id)


@router.patch("/{ticket_id}", response_model=TicketOut)
async def update_ticket(
    ticket_id: int,
    patch: TicketPatch,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    ticket = await get_ticket_or_404(db, ticket_id)

    if patch.status is not None:
        ticket.status = patch.status
    if patch.admin_notes is not None:
        ticket.admin_notes = patch.admin_notes
    if patch.admin_override_priority is not None:
        ticket.admin_override_priority = patch.admin_override_priority
    if patch.ai_draft_reply is not None:
        ticket.ai_draft_reply = patch.ai_draft_reply

    await commit_and_refresh(db, ticket)
    background_tasks.add_task(regenerate_briefing_background)
    return ticket


@router.post("/{ticket_id}/resolve", response_model=TicketOut)
async def resolve_ticket(
    ticket_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    ticket = await get_ticket_or_404(db, ticket_id)
    ticket.status = "resolved"
    await commit_and_refresh(db, ticket)
    background_tasks.add_task(regenerate_briefing_background)
    return ticket


@router.post("/{ticket_id}/dismiss", response_model=TicketOut)
async def dismiss_ticket(
    ticket_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    ticket = await get_ticket_or_404(db, ticket_id)
    ticket.status = "dismissed"
    await commit_and_refresh(db, ticket)
    background_tasks.add_task(regenerate_briefing_background)
    return ticket
