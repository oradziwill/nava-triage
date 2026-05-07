import json
import logging
from services.ai_clients import openai_client

logger = logging.getLogger(__name__)

TRIAGE_SYSTEM_PROMPT = """Jesteś asystentem AI polskiego administratora wspólnoty mieszkaniowej.
Analizujesz przychodzące wiadomości (email, SMS, głos) i klasyfikujesz je.

Zwróć TYLKO poprawny JSON, bez markdown, bez dodatkowego tekstu:
{
  "priority": "critical|high|medium|low",
  "category": "security|maintenance|billing|complaint|board|vendor|other",
  "sender_type": "resident|vendor|board|unknown",
  "summary": "1-2 zdania po polsku — co się dzieje i dlaczego to ważne",
  "reasoning": "dlaczego taki priorytet, co zadecydowało",
  "is_follow_up": true,
  "follow_up_signals": ["lista sygnałów że to follow-up, np. 'dwa razy dzwoniłem'"],
  "suggested_action": "jedno konkretne zdanie — co RM powinien zrobić jako pierwszy krok",
  "draft_reply": "gotowa odpowiedź w języku wiadomości, dostosowana do kanału (SMS = max 160 znaków, email = pełny)",
  "confidence": 0.0,
  "missing_info": ["czego brakuje żeby w pełni obsłużyć zgłoszenie"],
  "auto_escalate": false
}

Zasady priorytetu:
- critical: zalanie, pożar, brak ogrzewania zimą, zagrożenie bezpieczeństwa, awaria trwająca >24h z brakiem reakcji
- high: usterka wpływająca na wielu mieszkańców, ponowne zgłoszenie bez odpowiedzi
- medium: rozliczenia, pytania zarządu, skargi na sąsiadów
- low: pytania ogólne, informacje

Zasady auto_escalate:
- true jeśli: is_follow_up=true ORAZ priorytet był high, LUB kategoria security, LUB awaria trwa >48h"""


async def triage_message(channel: str, sender: str, subject: str | None, body: str) -> dict:
    client = openai_client()

    user_content = f"Kanał: {channel}\nNadawca: {sender}"
    if subject:
        user_content += f"\nTemat: {subject}"
    user_content += f"\n\nTreść:\n{body}"

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1024,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )

    raw = response.choices[0].message.content
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Triage JSON parse failed. Raw response: %s", raw)
        raise ValueError(f"Claude returned invalid JSON: {raw[:200]}")
