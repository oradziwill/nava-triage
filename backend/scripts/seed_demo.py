"""
Seed demo tickets via POST /api/ingest.
Run from repo root:  python backend/scripts/seed_demo.py
Or from backend/:    python scripts/seed_demo.py
"""
import time
import json
import urllib.request
import urllib.error
import os

BASE_URL = os.getenv("API_URL", "http://localhost:8002")

DEMO_MESSAGES = [
    {
        "channel": "email",
        "sender": "jan.kowalski@gmail.com",
        "subject": "Zepsuta brama — pilne",
        "body": "Brama do garażu podziemnego jest otwarta od 3 dni. Może wejść każdy. Dwa razy dzwoniłem, brak odpowiedzi.",
    },
    {
        "channel": "sms",
        "sender": "+48 601 234 567",
        "subject": None,
        "body": "Hej, przecieka sufit na klatce schodowej 3. piętro, robi się coraz gorzej",
    },
    {
        "channel": "email",
        "sender": "m.wisniewska@wp.pl",
        "subject": "Brak rozliczenia za marzec",
        "body": "Ani ja, ani sąsiadka z 14B nie dostałyśmy rozliczenia za marzec. Proszę o przesłanie.",
    },
    {
        "channel": "sms",
        "sender": "+48 799 112 233",
        "subject": None,
        "body": "Mieszkanie 4B znowu wynajmuje na Airbnb. To jest niezgodne z regulaminem wspólnoty. Co z tym będziecie robić?",
    },
    {
        "channel": "email",
        "sender": "zarzad@wspolnota-mokotow.pl",
        "subject": "Decyzja zarządu — remont dachu",
        "body": "Otrzymaliśmy trzy oferty na remont dachu. Zarząd musi podjąć decyzję przed kwietniowym zebraniem. Proszę o podsumowanie i rekomendację.",
    },
]


def post_json(url: str, data: dict) -> dict:
    payload = {k: v for k, v in data.items() if v is not None}
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def main():
    url = f"{BASE_URL}/api/ingest"
    print(f"Seeding {len(DEMO_MESSAGES)} tickets → {url}\n")

    for i, msg in enumerate(DEMO_MESSAGES, 1):
        print(f"[{i}/{len(DEMO_MESSAGES)}] {msg['channel'].upper()} from {msg['sender']}")
        if msg.get("subject"):
            print(f"         Subject: {msg['subject']}")
        print(f"         Body:    {msg['body'][:80]}...")

        try:
            result = post_json(url, msg)
            priority = result.get("priority", "?").upper()
            escalated = " ⚡ AUTO-ESCALATED" if result.get("escalated") else ""
            confidence = result.get("confidence")
            conf_str = f" (confidence: {confidence:.0%})" if confidence is not None else ""
            print(f"         → {priority}{escalated}{conf_str}")
            print(f"         Summary: {result.get('summary', '')}")
            print(f"         Action:  {result.get('suggested_action', '')}")
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"         ✗ HTTP {e.code}: {body}")
        except Exception as e:
            print(f"         ✗ Error: {e}")

        print()
        if i < len(DEMO_MESSAGES):
            time.sleep(1)

    print("Done.")


if __name__ == "__main__":
    main()
