# STRATEGY.md

## Gotowe — prototyp v0

### Triage AI

- Każda wiadomość (email, SMS, voicemail) jest automatycznie klasyfikowana przez GPT-4o
- Wynik triażu zawiera: priorytet (critical / high / medium / low), kategorię, typ nadawcy, podsumowanie, sugerowane działanie, szkic odpowiedzi, reasoning i poziom pewności
- Automatyczna eskalacja przy wykryciu sygnałów follow-up (np. „piszę po raz trzeci") i kategorii security

### Kolejka zgłoszeń

- Dashboard z listą aktywnych i rozwiązanych ticketów
- Filtrowanie po priorytecie i kategorii
- Karty zgłoszeń z kolorowym oznaczeniem priorytetu, wskaźnikiem eskalacji i ostrzeżeniem przy niskiej pewności AI
- Zakładka „Rozwiązane" z historią

### Panel szczegółów ticketu

- Pełna treść oryginalnej wiadomości
- Podsumowanie i reasoning AI
- Edytowalny szkic odpowiedzi i notatki administratora
- Ręczna zmiana priorytetu (override)
- Lista zadań (checkbox, dodawanie przez UI i przez głos)
- Przyciski: wyślij odpowiedź / rozwiąż / odrzuć

### Voice briefing

- Jeden przycisk odtwarza ~40-sekundowe podsumowanie aktywnych zgłoszeń w języku polskim (ElevenLabs TTS)
- Briefing generuje się automatycznie po każdej zmianie w ticketach i jest cache'owany
- Oddzielne intro z datą i liczbą krytycznych spraw

### Komendy głosowe

- Nagrywanie przez mikrofon (maks. 30 sek.), transkrypcja Whisper, rozpoznanie intencji przez GPT-4o
- Obsługiwane komendy: eskaluj, rozwiąż, dodaj notatkę, dodaj zadanie, stwórz ticket, wezwij serwis
- Potwierdzenie głosowe po wykonaniu akcji

### Infrastruktura

- Docker Compose: PostgreSQL 16 + FastAPI + React/Vite (hot-reload w dev)
- REST API z endpointami: ingest, tickets CRUD, voice briefing, voice command
- Seed data: 16 realistycznych wiadomości po polsku (różne kanały, priorytety, eskalacje)

---

## Tydzień 1 — wersja demo

- Podłączenie prawdziwego Gmaila jednego RM zamiast seed data
- Obsługa realnych maili: cytaty, stopki, forwardy, chaos w treści
- Voice briefing przetestowany na minimum 10 zestawach ticketów
- Naturalnie brzmiący voice briefing zamiast syntetycznego odczytu listy
- Stabilna obsługa 5 komend głosowych:
  - stwórz ticket
  - eskaluj
  - zamknij
  - dodaj notatkę
  - wezwij serwis
- Jeden pełny scenariusz end-to-end:
  - SMS o zalaniu
  - triage AI
  - voice briefing
  - komenda głosowa RM
  - zamknięcie ticketu
- Wyjaśnienie decyzji AI dostępne przy eskalacji
- Spedzenie czasu z administratorem w celu zweryfikowania jak wyglada jego day to day job, z jakimi problemami sie zmaga, na czym warto sie skupic przy rozwoju produktu

---

## Miesiąc 1 — codzienne użycie przez RM

- Integracja SMS przez Twilio
- Obsługa voicemail przez Whisper
- Domknięcie wszystkich głównych kanałów wejściowych
- Minimalna baza mieszkańców:
  - imię i nazwisko
  - numer mieszkania
  - numer telefonu
- Automatyczne dopasowanie mieszkańca z voicemaila do istniejącego profilu
- Wysyłka draftów bezpośrednio z systemu
- Historia zgłoszeń per mieszkaniec
- Widoczność wcześniejszych problemów i powtarzających się zgłoszeń
- Podstawowe metryki dla RM:
  - średni czas odpowiedzi
  - liczba zamkniętych ticketów
  - backlog
  - liczba eskalacji
- Zbieranie feedbacku do poprawy promptów i klasyfikacji

---

## Najtrudniejsze problemy

### 1. Zaufanie przy high-stakes decyzjach

- Odpowiedzialność prawna i operacyjna po stronie RM
- Ryzyko błędnej klasyfikacji zgłoszeń krytycznych
- Konieczność pełnej transparentności decyzji AI
- Widoczny reasoning dla każdej decyzji
- Override jednym kliknięciem
- Audit log wszystkich zmian wykonanych przez AI i użytkownika

---

### 2. Jakość brudnych danych

- Urwane voicemaile
- SMS-y bez kontekstu
- Długie chainy mailowe
- Nieczytelne zgłoszenia mieszkańców
- Znacznie gorsza jakość danych niż w seed data
- Testowanie na prawdziwych danych od pierwszego tygodnia
- Unikanie developmentu wyłącznie na danych demo

---

### 3. Adopcja systemu

- Wieloletnie przyzwyczajenie RM do Excela i Outlooka
- Ryzyko powrotu do starego workflow przy większym friction
- Konieczność szybszego pierwszego doświadczenia niż obecny proces
- Minimalizacja liczby kliknięć
- Zero-friction onboarding
- Voice briefing jako naturalny punkt wejścia do produktu

---

### 4. Skalowanie po M&A

- Różne workflowy między firmami
- Różne nazewnictwo statusów i priorytetów
- Brak uniwersalnego promptu działającego dla wszystkich klientów
- Potrzeba konfiguracji per klient
- Osobne reguły klasyfikacji
- Onboarding na rzeczywistych danych przed go-live

---

### 5. Nadużywanie kanału głosowego

- Rozmowy niezwiązane ze zgłoszeniami
- Wysokie koszty:
  - ElevenLabs
  - Whisper
  - API modeli LLM
- Szum w systemie ticketowym
- Problem z naturalnym kończeniem rozmów przez AI
- Twardy limit czasu rozmowy
- Prompt kierujący użytkownika do konkretu
- Wykrywanie braku realnego zgłoszenia
- Automatyczne zakończenie rozmowy po kilku turach bez identyfikowalnego problemu
- Przekierowanie do alternatywnego kanału kontaktu
