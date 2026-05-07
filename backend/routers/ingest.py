from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database import get_db
from models.ticket import Ticket
from services.triage import triage_message
from services.briefing_generator import regenerate_briefing_background

router = APIRouter(prefix="/api", tags=["ingest"])


class IngestRequest(BaseModel):
    channel: str = "email"
    sender: str
    subject: Optional[str] = None
    body: str


@router.post("/ingest", status_code=201)
async def ingest_message(
    payload: IngestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    try:
        triage = await triage_message(
            channel=payload.channel,
            sender=payload.sender,
            subject=payload.subject,
            body=payload.body,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Triage failed: {str(e)}")

    priority = triage.get("priority", "medium")
    escalated = False

    if triage.get("auto_escalate") and priority == "high":
        priority = "critical"
        escalated = True
        triage["reasoning"] = triage.get("reasoning", "") + " [AUTO-ESKALACJA: follow-up bez odpowiedzi]"

    ticket = Ticket(
        channel=payload.channel,
        sender=payload.sender,
        sender_type=triage.get("sender_type", "unknown"),
        subject=payload.subject,
        body_raw=payload.body,
        priority=priority,
        category=triage.get("category", "other"),
        status="new",
        ai_title=triage.get("title"),
        ai_summary=triage.get("summary"),
        ai_draft_reply=triage.get("draft_reply"),
        ai_reasoning=triage.get("reasoning"),
        ai_suggested_action=triage.get("suggested_action"),
        ai_missing_info=triage.get("missing_info") or [],
        ai_follow_up_signals=triage.get("follow_up_signals") or [],
        confidence=triage.get("confidence"),
        escalated=escalated,
        follow_up_count=1 if triage.get("is_follow_up") else 0,
    )

    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)

    background_tasks.add_task(regenerate_briefing_background)

    return {
        "id": ticket.id,
        "priority": ticket.priority,
        "category": ticket.category,
        "sender_type": ticket.sender_type,
        "escalated": ticket.escalated,
        "summary": ticket.ai_summary,
        "suggested_action": ticket.ai_suggested_action,
        "confidence": ticket.confidence,
    }
