from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, JSON, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


SHORT_TEXT_LEN = 20
MEDIUM_TEXT_LEN = 30
LONG_TEXT_LEN = 255
SUBJECT_TEXT_LEN = 500


def short_text_column(**kwargs):
    return mapped_column(String(SHORT_TEXT_LEN), **kwargs)


def timestamp_column(*, on_update: bool = False):
    options = {"server_default": func.now()}
    if on_update:
        options["onupdate"] = func.now()
    return mapped_column(DateTime(timezone=True), **options)


class Ticket(Base):
    __tablename__ = "tickets"

    # Metadata
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = timestamp_column()
    updated_at: Mapped[datetime] = timestamp_column(on_update=True)

    # Source
    channel: Mapped[str] = short_text_column()  # email | sms | voice
    sender: Mapped[Optional[str]] = mapped_column(String(LONG_TEXT_LEN))  # raw sender (email or phone)
    sender_type: Mapped[str] = short_text_column(default="unknown")

    # Ticket content
    subject: Mapped[Optional[str]] = mapped_column(String(SUBJECT_TEXT_LEN))
    body_raw: Mapped[Optional[str]] = mapped_column(Text)

    # Routing state
    priority: Mapped[str] = short_text_column(default="medium")
    category: Mapped[str] = mapped_column(String(MEDIUM_TEXT_LEN), default="other")
    status: Mapped[str] = short_text_column(default="new")

    # AI-generated fields
    ai_title: Mapped[Optional[str]] = mapped_column(String(LONG_TEXT_LEN))
    ai_summary: Mapped[Optional[str]] = mapped_column(Text)
    ai_draft_reply: Mapped[Optional[str]] = mapped_column(Text)
    ai_reasoning: Mapped[Optional[str]] = mapped_column(Text)
    ai_suggested_action: Mapped[Optional[str]] = mapped_column(Text)
    ai_missing_info: Mapped[Optional[list]] = mapped_column(JSON)
    ai_follow_up_signals: Mapped[Optional[list]] = mapped_column(JSON)
    confidence: Mapped[Optional[float]] = mapped_column(Float)

    # Human override fields
    admin_override_priority: Mapped[Optional[str]] = short_text_column()
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Tasks — list of {id: str, text: str, done: bool}
    tasks: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=None)

    # Workflow counters
    follow_up_count: Mapped[int] = mapped_column(Integer, default=0)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
