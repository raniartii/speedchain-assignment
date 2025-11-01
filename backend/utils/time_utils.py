from datetime import datetime, timedelta, timezone
import re

# Asia/Kolkata (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def to_local_date_str(dt_local: datetime) -> str:
    return dt_local.astimezone(IST).strftime("%Y-%m-%d")

def parse_local_iso(local_iso: str) -> datetime:
    """
    Expects ISO with tz offset like '2025-11-01T17:00:00+05:30'
    """
    dt = datetime.fromisoformat(local_iso)
    # If no tz info, assume IST
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=IST)
    return dt.astimezone(IST).replace(minute=0, second=0, microsecond=0)

def _parse_time_phrase(text: str) -> datetime | None:
    """
    Supports 'today 5 pm', 'tomorrow at 17:00', '1 nov 5pm', 'on 2/11 at 6pm', etc.
    Normalizes to start-of-hour.
    """
    t = text.lower()
    now = datetime.now(IST)
    day = now.date()

    # tomorrow / today
    if "tomorrow" in t:
        day = (now + timedelta(days=1)).date()
    elif "today" in t:
        day = now.date()

    # explicit dd/mm or dd-mon
    # very permissive; we only need rough demo parsing
    m_date = re.search(r"\b(\d{1,2})[\/\-\s](\d{1,2})(?:[\/\-\s](\d{2,4}))?\b", t)
    if m_date:
        d = int(m_date.group(1))
        m = int(m_date.group(2))
        y = int(m_date.group(3)) if m_date.group(3) else now.year
        try:
            day = datetime(y, m, d, tzinfo=IST).date()
        except Exception:
            pass

    # time
    # 17:00, 5pm, 5 pm, 05:00 pm
    hour = None
    m_time_24 = re.search(r"\b([01]?\d|2[0-3]):?([0-5]\d)?\b", t)
    m_time_ampm = re.search(r"\b(\d{1,2})(?:\:(\d{2}))?\s*(am|pm)\b", t)
    if m_time_ampm:
        h = int(m_time_ampm.group(1))
        mer = m_time_ampm.group(3)
        if mer == "pm" and h != 12:
            h += 12
        if mer == "am" and h == 12:
            h = 0
        hour = h
    elif m_time_24:
        hour = int(m_time_24.group(1))

    if hour is None:
        return None

    return datetime(day.year, day.month, day.day, hour=hour, tzinfo=IST).replace(minute=0, second=0, microsecond=0)

def parse_user_time_to_local_slot(text: str) -> str | None:
    dt = _parse_time_phrase(text)
    if not dt:
        return None
    # clamp to business hours 08..21 start
    if dt.hour < 8 or dt.hour > 21:
        return None
    return dt.isoformat()

def next_slots_nearby(slot: datetime, hours: int = 2):
    out = []
    for delta in range(1, hours + 1):
        # +/- delta hours
        before = slot - timedelta(hours=delta)
        after  = slot + timedelta(hours=delta)
        if 8 <= before.hour <= 21:
            out.append(before)
        if 8 <= after.hour <= 21:
            out.append(after)
    # unique and sorted by proximity
    uniq = sorted({s for s in out}, key=lambda d: abs((d - slot).total_seconds()))
    return uniq

def normalize_table_type(val: str) -> str:
    v = val.lower().strip()
    if v in ("small", "2", "two", "couple"):
        return "small"
    return "group"
