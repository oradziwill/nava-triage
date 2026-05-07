import io
import math
import asyncio
from openai import OpenAI
from config import settings


def _transcribe_sync(audio_bytes: bytes, filename: str) -> dict:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    buf = io.BytesIO(audio_bytes)
    buf.name = filename

    response = client.audio.transcriptions.create(
        model="whisper-1",
        file=buf,
        language="pl",
        response_format="verbose_json",
    )

    confidence = None
    if hasattr(response, "segments") and response.segments:
        avg_logprob = sum(s.avg_logprob for s in response.segments) / len(response.segments)
        confidence = round(min(1.0, max(0.0, math.exp(avg_logprob))), 2)

    return {
        "transcript": response.text,
        "language": getattr(response, "language", "pl"),
        "confidence": confidence,
    }


async def transcribe_audio(audio_bytes: bytes, filename: str) -> dict:
    return await asyncio.to_thread(_transcribe_sync, audio_bytes, filename)
