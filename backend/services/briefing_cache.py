from dataclasses import dataclass
from datetime import datetime

@dataclass
class BriefingCache:
    audio_bytes: bytes | None = None
    generated_at: datetime | None = None
    ticket_count: int = 0
    is_generating: bool = False
    script_text: str | None = None

_cache = BriefingCache()

def get_cache() -> BriefingCache:
    return _cache
