"""US equity regular trading hours (09:30-16:00 America/New_York, Monday-Friday).

Exchange holidays are not modeled: a holiday counts as RTH, so a quiet feed on a
holiday burns error budget. That is a known, documented limitation (see ADR 0004);
the fix is a holiday calendar, not a looser SLO.
"""

from datetime import datetime, time
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
OPEN = time(9, 30)
CLOSE = time(16, 0)


def in_rth(now: datetime) -> bool:
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    local = now.astimezone(NY)
    return local.weekday() < 5 and OPEN <= local.time() < CLOSE
