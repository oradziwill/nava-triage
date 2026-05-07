from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Boolean, DateTime, Float, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    channel: Mapped[str] = mapped_column(String(20))          # email | sms | voice
    sender: Mapped[Optional[str]] = mapped_column(String(255)) # raw sender (email or phone)
    sender_type: Mapped[str] = mapped_column(String(20), default="unknown")

    subject: Mapped[Optional[str]] = mapped_column(String(500))
    body_raw: Mapped[Optional[str]] = mapped_column(Text)

    priority: Mapped[str] = mapped_column(String(20), default="medium")
    category: Mapped[str] = mapped_column(String(30), default="other")
    status: Mapped[str] = mapped_column(String(20), default="new")

    ai_summary: Mapped[Optional[str]] = mapped_column(Text)
    ai_draft_reply: Mapped[Optional[str]] = mapped_column(Text)
    ai_reasoning: Mapped[Optional[str]] = mapped_column(Text)
    ai_suggested_action: Mapped[Optional[str]] = mapped_column(Text)
    ai_missing_info: Mapped[Optional[list]] = mapped_column(JSON)
    ai_follow_up_signals: Mapped[Optional[list]] = mapped_column(JSON)
    confidence: Mapped[Optional[float]] = mapped_column(Float)

    admin_override_priority: Mapped[Optional[str]] = mapped_column(String(20))
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)

    follow_up_count: Mapped[int] = mapped_column(Integer, default=0)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
