from __future__ import annotations

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from . import models

KAMPALA_TZ = ZoneInfo("Africa/Kampala")
DEFAULT_REFRESH_NAME = "pipeline"


def now_iso() -> str:
    return datetime.now(KAMPALA_TZ).isoformat(timespec="seconds")


def record_refresh_state(db, name: str, status: str, details: Optional[str] = None, refreshed_at: Optional[str] = None):
    state = db.query(models.DataRefreshState).filter(models.DataRefreshState.name == name).first()
    if not state:
        state = models.DataRefreshState(name=name)
        db.add(state)

    state.refreshed_at = refreshed_at or now_iso()
    state.status = status
    state.details = details[:1000] if details else None
    return state


def get_refresh_state(db, name: str = DEFAULT_REFRESH_NAME):
    return db.query(models.DataRefreshState).filter(models.DataRefreshState.name == name).first()


def format_refresh_timestamp(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(value)
    except Exception:
        return value

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KAMPALA_TZ)
    else:
        parsed = parsed.astimezone(KAMPALA_TZ)

    return parsed.strftime("%d %b %Y, %I:%M %p EAT")


def build_refresh_label(value: Optional[str]) -> Optional[str]:
    formatted = format_refresh_timestamp(value)
    if not formatted:
        return None
    return f"Fresh as of {formatted}"

