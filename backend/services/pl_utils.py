"""Polish text utilities for TTS — numbers, dates, noun inflection."""
import re

_UNITS = [
    "zero", "jeden", "dwa", "trzy", "cztery", "pięć",
    "sześć", "siedem", "osiem", "dziewięć", "dziesięć",
    "jedenaście", "dwanaście", "trzynaście", "czternaście", "piętnaście",
    "szesnaście", "siedemnaście", "osiemnaście", "dziewiętnaście",
]
_TENS = [
    "", "", "dwadzieścia", "trzydzieści", "czterdzieści", "pięćdziesiąt",
    "sześćdziesiąt", "siedemdziesiąt", "osiemdziesiąt", "dziewięćdziesiąt",
]
_HUNDREDS = [
    "", "sto", "dwieście", "trzysta", "czterysta", "pięćset",
    "sześćset", "siedemset", "osiemset", "dziewięćset",
]

# Ordinal nominative — for spoken dates: "siódmy maja"
_ORDINALS_NOM = [
    "", "pierwszy", "drugi", "trzeci", "czwarty", "piąty",
    "szósty", "siódmy", "ósmy", "dziewiąty", "dziesiąty",
    "jedenasty", "dwunasty", "trzynasty", "czternasty", "piętnasty",
    "szesnasty", "siedemnasty", "osiemnasty", "dziewiętnasty", "dwudziesty",
    "dwudziesty pierwszy", "dwudziesty drugi", "dwudziesty trzeci",
    "dwudziesty czwarty", "dwudziesty piąty", "dwudziesty szósty",
    "dwudziesty siódmy", "dwudziesty ósmy", "dwudziesty dziewiąty",
    "trzydziesty", "trzydziesty pierwszy",
]

_MONTHS_SPOKEN = [
    "", "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
    "lipca", "sierpnia", "września", "października", "listopada", "grudnia",
]
_MONTHS_BUILD = [
    "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
    "lipca", "sierpnia", "września", "października", "listopada", "grudnia",
]
_DAYS_PL = [
    "poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela",
]


def pl_cardinal(n: int) -> str:
    """Convert integer to Polish cardinal word(s). Works up to 999."""
    if n < 0:
        return f"minus {pl_cardinal(-n)}"
    if n < 20:
        return _UNITS[n]
    if n < 100:
        tens, units = divmod(n, 10)
        parts = [_TENS[tens]]
        if units:
            parts.append(_UNITS[units])
        return " ".join(parts)
    hundreds, rest = divmod(n, 100)
    parts = [_HUNDREDS[hundreds]]
    if rest:
        parts.append(pl_cardinal(rest))
    return " ".join(parts)


def pl_ordinal_day(day: int) -> str:
    """Return nominative ordinal for a day-of-month: 7 → 'siódmy'."""
    if 1 <= day <= 31:
        return _ORDINALS_NOM[day]
    return pl_cardinal(day)


def pl_inflect(n: int, one: str, few: str, many: str) -> str:
    """
    Polish noun inflection for counts:
      n=1          → one  (e.g. 'zgłoszenie')
      n=2,3,4      → few  (e.g. 'zgłoszenia')
      n=5+         → many (e.g. 'zgłoszeń')
    Exception: 12-14 always → many.
    """
    if n % 100 in (12, 13, 14):
        return many
    mod = n % 10
    if mod == 1:
        return one
    if mod in (2, 3, 4):
        return few
    return many


def pl_tickets(n: int) -> str:
    """'jedno zgłoszenie', 'dwa zgłoszenia', 'pięć zgłoszeń'."""
    word = "jedno" if n == 1 else pl_cardinal(n)
    noun = pl_inflect(n, "zgłoszenie", "zgłoszenia", "zgłoszeń")
    return f"{word} {noun}"


def pl_critical(n: int) -> str:
    """'jedno krytyczne', 'dwa krytyczne', 'pięć krytycznych'."""
    word = "jedno" if n == 1 else pl_cardinal(n)
    noun = pl_inflect(n, "krytyczne", "krytyczne", "krytycznych")
    return f"{word} {noun}"


def polish_date_spoken() -> tuple[str, str, str]:
    """Return (weekday_str, day_ordinal, month_spoken) for today."""
    from datetime import datetime
    now = datetime.now()
    weekday = _DAYS_PL[now.weekday()]
    day     = pl_ordinal_day(now.day)
    month   = _MONTHS_SPOKEN[now.month]
    return weekday, day, month


def polish_date_for_prompt() -> tuple[str, str, str]:
    """Return (weekday_str, day_int_str, month_name) for prompt context."""
    from datetime import datetime
    now = datetime.now()
    return _DAYS_PL[now.weekday()], str(now.day), _MONTHS_BUILD[now.month - 1]


def normalize_for_tts(text: str) -> str:
    """Replace digit sequences with Polish spoken words so TTS reads them naturally."""
    return re.sub(r'\b\d+\b', lambda m: pl_cardinal(int(m.group())), text)
