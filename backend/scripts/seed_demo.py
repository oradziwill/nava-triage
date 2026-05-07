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
    {
        "channel": "sms",
        "sender": "+48 512 887 001",
        "subject": None,
        "body": "Pani Ania nie odpowiada od tygodnia na moje maile w sprawie funduszu remontowego",
    },
    {
        "channel": "email",
        "sender": "p.nowak@gmail.com",
        "subject": "Skargi na hałas — mieszkanie 12A",
        "body": "To już czwarta skarga na to mieszkanie. Głośna muzyka każdą noc po północy. Nic nie zostało zrobione.",
    },
    {
        "channel": "sms",
        "sender": "+48 604 332 119",
        "subject": None,
        "body": "Winda znowu zepsuta w budynku B. Trzeci raz w tym miesiącu.",
    },
    {
        "channel": "email",
        "sender": "r.dabrowska@onet.pl",
        "subject": "Odnowienie ubezpieczenia",
        "body": "Ubezpieczenie budynku kończy się 30 kwietnia. Nie widzę tego w agendzie zebrania. Kto się tym zajmuje?",
    },
    {
        "channel": "sms",
        "sender": "+48 733 201 445",
        "subject": None,
        "body": "Czy ktoś może potwierdzić, że moja wpłata na fundusz eksploatacyjny dotarła? Zapłaciłem 3 tygodnie temu.",
    },
    {
        "channel": "email",
        "sender": "jan.kowalski@gmail.com",
        "subject": "RE: Zepsuta brama",
        "body": "Piszę PO RAZ TRZECI. Brama nadal otwarta. Jeśli do końca tygodnia nic się nie zmieni, zgłaszam sprawę do nadzoru budowlanego.",
    },
    {
        "channel": "sms",
        "sender": "+48 601 234 567",
        "subject": None,
        "body": "O tej przeciekającej klatce schodowej co pisałem — teraz leje się na skrzynkę elektryczną. To chyba groźne?",
    },
    {
        "channel": "voicemail",
        "sender": "+48 888 100 200",
        "subject": None,
        "body": "[Transkrypcja Whisper, pewność ~72%] Dzień dobry, dzwonię... chyba Lewandowska z... [nieczytelne]... bo proszę pani, w piwnicy jest woda na... nie wiem... dwadzieścia centymetrów? Może więcej. I śmierdzi. Proszę o... [nieczytelne]... jak najszybciej.",
    },
    {
        "channel": "email",
        "sender": "biuro@bud-serwis.pl",
        "subject": "Faktura nr FS/2024/0892",
        "body": "W załączniku przesyłam fakturę za przegląd instalacji gazowej (budynki A–C). Kwota 8.200 zł netto. Proszę o potwierdzenie lub zgłoszenie korekt w ciągu 7 dni roboczych.",
    },
    {
        "channel": "email",
        "sender": "tomek.zielinski@outlook.com",
        "subject": "Quick question about the parking spot",
        "body": "Hi, I just moved in (apt 7C) and my Polish is still not great. Is there a way to rent an additional parking spot in the garage? Also the intercom doesn't seem to work for my unit. Thanks!",
    },
    {
        "channel": "sms",
        "sender": "+48 606 999 111",
        "subject": None,
        "body": "Cześć, z tego co wiem to pani z 8A też ma zalany sufit, chyba ten sam problem co u mnie na 3 piętrze. Może warto sprawdzić całą pionówkę?",
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
