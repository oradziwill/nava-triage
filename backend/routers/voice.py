import base64
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.ticket import Ticket
from services.briefing_cache import get_cache
from services.briefing_generator import regenerate_briefing_background
from services.pl_utils import polish_date_spoken, normalize_for_tts
from services.elevenlabs import synthesize_speech, build_intro_text
from services.whisper import transcribe_audio
from services.intent import interpret_voice_command

router = APIRouter(prefix="/api/voice", tags=["voice"])

_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_CACHE_TTL_SECONDS = 1800  # 30 min
_PRIORITY_PL = {"critical": "krytyczny", "high": "wysoki", "medium": "średni", "low": "niski"}


# ── GET /api/voice/briefing ─────────────────────────────────────────────────

@router.get("/briefing")
async def get_briefing():
    cache = get_cache()
    if cache.audio_bytes and cache.generated_at:
        age = (datetime.now() - cache.generated_at).total_seconds()
        if age < _CACHE_TTL_SECONDS:
            return Response(
                content=cache.audio_bytes,
                media_type="audio/mpeg",
                headers={"Content-Disposition": "inline; filename=briefing.mp3"},
            )
    return JSONResponse({"status": "generating", "retry_after": 8}, status_code=202)


# ── GET /api/voice/briefing/status ─────────────────────────────────────────

@router.get("/briefing/status")
async def briefing_status():
    cache = get_cache()
    return {
        "ready": cache.audio_bytes is not None and cache.generated_at is not None,
        "generated_at": cache.generated_at.isoformat() if cache.generated_at else None,
        "ticket_count": cache.ticket_count,
        "is_generating": cache.is_generating,
        "script_preview": (cache.script_text or "")[:120] or None,
    }


# ── GET /api/voice/intro ────────────────────────────────────────────────────

@router.get("/intro")
async def get_intro(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Ticket).where(Ticket.status.notin_(["resolved", "dismissed"]))
    )
    tickets = result.scalars().all()
    total    = len(tickets)
    critical = sum(1 for t in tickets if (t.admin_override_priority or t.priority) == "critical")

    weekday, day_ordinal, month = polish_date_spoken()
    date_str = f"{day_ordinal} {month}, {weekday}"
    text = build_intro_text(date_str, total, critical)

    try:
        audio = await synthesize_speech(text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Intro synthesis failed: {e}")

    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=intro.mp3"},
    )


# ── POST /api/voice/interpret ───────────────────────────────────────────────

@router.post("/interpret")
async def interpret_voice(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    try:
        whisper = await transcribe_audio(audio_bytes, audio.filename or "recording.webm")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Transcription failed: {e}")

    transcript = whisper["transcript"].strip()
    if not transcript:
        raise HTTPException(status_code=422, detail="Empty transcription result")

    try:
        intent = await interpret_voice_command(transcript)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Intent extraction failed: {e}")

    return {
        "transcript": transcript,
        "intent": intent,
        "whisper_confidence": whisper.get("confidence"),
    }


# ── POST /api/voice/command ─────────────────────────────────────────────────

@router.post("/command")
async def voice_command(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    audio: UploadFile = File(...),
    context_ticket_id: Optional[int] = Form(None),
):
    # 1. Transcribe
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    try:
        whisper = await transcribe_audio(audio_bytes, audio.filename or "recording.webm")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Transcription failed: {e}")

    transcript = whisper["transcript"].strip()
    if not transcript:
        raise HTTPException(status_code=422, detail="Empty transcription result")

    # 2. Build context for intent extraction
    context_ticket: Optional[Ticket] = None
    context_text: Optional[str] = None

    if context_ticket_id:
        context_ticket = await db.get(Ticket, context_ticket_id)
        if context_ticket:
            context_text = (
                f"Aktywne zgłoszenie ID {context_ticket.id}: "
                f"{context_ticket.subject or '(brak tematu)'}, "
                f"priorytet {context_ticket.priority}, "
                f"kategoria {context_ticket.category}. "
                f"Podsumowanie: {context_ticket.ai_summary or '(brak)'}"
            )
    else:
        result = await db.execute(
            select(Ticket)
            .where(Ticket.status.notin_(["resolved", "dismissed"]))
            .limit(10)
        )
        active = result.scalars().all()
        if active:
            summaries = "; ".join(
                f"[{t.id}] {t.subject or t.ai_summary or '(brak)'} ({t.priority})"
                for t in active
            )
            context_text = f"Aktywne zgłoszenia: {summaries}"

    # 3. Extract intent
    try:
        intent = await interpret_voice_command(transcript, context_text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Intent extraction failed: {e}")

    intent_type = intent.get("intent", "unknown")
    confidence = intent.get("confidence", 0.0)

    action_taken = "none"
    affected_ticket_id: Optional[int] = None
    confirmation_text = "Nie zrozumiałem polecenia. Powiedz jeszcze raz lub opisz dokładniej."

    # 4. Execute action
    if intent_type == "unknown" or confidence < 0.4:
        pass  # keep default confirmation_text

    elif intent_type in ("escalate", "resolve", "add_note") and not context_ticket_id:
        confirmation_text = "Nie wiem o które zgłoszenie chodzi. Otwórz sprawę i spróbuj ponownie."

    elif intent_type == "escalate":
        if not context_ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        context_ticket.admin_override_priority = "critical"
        note = "Eskalowano głosowo przez RM"
        context_ticket.admin_notes = (
            (context_ticket.admin_notes + "\n" + note).strip()
            if context_ticket.admin_notes else note
        )
        context_ticket.escalated = True
        await db.commit()
        await db.refresh(context_ticket)
        background_tasks.add_task(regenerate_briefing_background)
        action_taken = "escalated"
        affected_ticket_id = context_ticket.id
        subj = context_ticket.subject or context_ticket.ai_summary or "zgłoszenie"
        confirmation_text = f"Gotowe. Eskalowałem sprawę do priorytetu krytycznego: {subj}."

    elif intent_type == "resolve":
        if not context_ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        context_ticket.status = "resolved"
        await db.commit()
        await db.refresh(context_ticket)
        background_tasks.add_task(regenerate_briefing_background)
        action_taken = "resolved"
        affected_ticket_id = context_ticket.id
        confirmation_text = "Gotowe. Oznaczyłem zgłoszenie jako rozwiązane."

    elif intent_type == "add_note":
        if not context_ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        note = "[GŁOSOWE] " + transcript
        context_ticket.admin_notes = (
            (context_ticket.admin_notes + "\n" + note).strip()
            if context_ticket.admin_notes else note
        )
        await db.commit()
        await db.refresh(context_ticket)
        background_tasks.add_task(regenerate_briefing_background)
        action_taken = "note_added"
        affected_ticket_id = context_ticket.id
        confirmation_text = "Gotowe. Dodałem notatkę do zgłoszenia."

    elif intent_type in ("create_ticket", "call_vendor"):
        suggested = intent.get("suggested_ticket") or {}
        entities  = intent.get("entities") or {}
        category  = "vendor" if intent_type == "call_vendor" else suggested.get("category", "other")
        priority  = suggested.get("priority", "medium")

        body_parts = ["[GŁOSOWE] " + transcript]
        if entities.get("building"):
            body_parts.append(f"Budynek: {entities['building']}")
        if entities.get("apartment"):
            body_parts.append(f"Mieszkanie: {entities['apartment']}")

        new_ticket = Ticket(
            channel="voice",
            sender="RM (voice)",
            sender_type="board",
            subject=intent.get("summary") or transcript[:80],
            body_raw="\n".join(body_parts),
            priority=priority,
            category=category,
            status="new",
            ai_summary=intent.get("human_readable"),
            ai_suggested_action=suggested.get("body"),
            escalated=False,
            follow_up_count=0,
        )
        db.add(new_ticket)
        await db.commit()
        await db.refresh(new_ticket)
        background_tasks.add_task(regenerate_briefing_background)
        action_taken = "created_ticket"
        affected_ticket_id = new_ticket.id

        detail_parts = []
        if entities.get("vendor_type"):
            detail_parts.append(entities["vendor_type"])
        if entities.get("building"):
            detail_parts.append(f"budynek {entities['building']}")
        detail = ", ".join(detail_parts) if detail_parts else (intent.get("summary") or transcript[:40])
        confirmation_text = (
            f"Gotowe. Utworzyłem zgłoszenie: {detail}, "
            f"priorytet {_PRIORITY_PL.get(priority, priority)}."
        )

    # 5. Synthesize confirmation audio
    tts_text = normalize_for_tts(confirmation_text)
    audio_b64: Optional[str] = None
    try:
        audio_out = await synthesize_speech(tts_text)
        audio_b64 = base64.b64encode(audio_out).decode()
    except Exception:
        pass  # audio is optional — UI can fall back to text

    return {
        "transcript": transcript,
        "intent": intent,
        "action_taken": action_taken,
        "affected_ticket_id": affected_ticket_id,
        "confirmation_text": confirmation_text,
        "confirmation_audio": audio_b64,
    }
