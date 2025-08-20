from __future__ import annotations

from datetime import datetime

ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def now_iso() -> str:
    return datetime.utcnow().strftime(ISO_FORMAT)


def parse_iso(value: str) -> datetime:
    return datetime.strptime(value, ISO_FORMAT)
