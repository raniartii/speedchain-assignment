# backend/services/booking_service.py
"""
Booking service for BrewHub Café

- JSON persistence in data/bookings.json (no DB).
- Availability per local (IST) hourly slot between 08:00–22:00.
- Capacity enforcement: small (10 tables), group (4 tables).
- Nearby alternatives when slot is full.
- Sends premium confirmation email via email_service.send_booking_confirmation.
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from backend.utils.time_utils import IST, to_local_date_str, parse_local_iso, next_slots_nearby
from backend.utils.storage import atomic_save_json
from backend.services.email_service import send_booking_confirmation

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
BOOKINGS_FILE = DATA_DIR / "bookings.json"

# Exported capacity constant (used by other modules if needed)
CAPACITY: Dict[str, int] = {
    "small": 10,   # number of 2-seater tables
    "group": 4     # number of 5-seater tables
}


# ----------------------------- storage helpers -----------------------------

def _ensure_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not BOOKINGS_FILE.exists():
        BOOKINGS_FILE.write_text("[]", encoding="utf-8")


def _load_bookings() -> List[Dict[str, Any]]:
    _ensure_files()
    try:
        return json.loads(BOOKINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_bookings(bookings: List[Dict[str, Any]]) -> None:
    _ensure_files()
    atomic_save_json(BOOKINGS_FILE, bookings)


# ----------------------------- time/keys helpers ---------------------------

def _slot_key_local(dt: datetime) -> str:
    """
    Key by local hour bucket (YYYY-mm-ddTHH:00+0530). Truncates to hour.
    """
    local = dt.astimezone(IST).replace(minute=0, second=0, microsecond=0)
    return local.isoformat()


def _same_local_hour(dt_a: datetime, dt_b: datetime) -> bool:
    a = dt_a.astimezone(IST).replace(minute=0, second=0, microsecond=0)
    b = dt_b.astimezone(IST).replace(minute=0, second=0, microsecond=0)
    return a == b


def generate_day_slots(date_local: datetime) -> List[datetime]:
    """
    Generate local hourly start times [08:00 ... 21:00] for a given local date.
    The booking window is 1 hour; last booking 21:00–22:00.
    """
    start = date_local.astimezone(IST).replace(hour=8, minute=0, second=0, microsecond=0)
    slots: List[datetime] = []
    for h in range(8, 22):  # 8..21 inclusive
        slots.append(start.replace(hour=h))
    return slots


# ----------------------------- availability --------------------------------

def availability_for_date(date_iso: str) -> Dict[str, Any]:
    """
    date_iso: 'YYYY-mm-dd' (local date)
    Returns available table counts for each slot of that date.
    """
    # Build the list of local slots for that date
    date_local = datetime.fromisoformat(date_iso).replace(tzinfo=IST)
    slots = generate_day_slots(date_local)
    bookings = _load_bookings()

    # Prepare counters per slot_key
    counters: Dict[str, Dict[str, int]] = {}
    for s in slots:
        key = _slot_key_local(s)
        counters[key] = {"small": 0, "group": 0}

    # Count bookings that fall on this date (local) per slot + table type
    for b in bookings:
        try:
            b_slot = parse_local_iso(b["slot_iso"])  # local-aware dt
        except Exception:
            continue
        if b_slot.date() != date_local.date():
            continue
        key = _slot_key_local(b_slot)
        ttype = b.get("table_type", "small")
        if key in counters and ttype in counters[key]:
            counters[key][ttype] += 1

    out = []
    for s in slots:
        key = _slot_key_local(s)
        taken_small = counters[key]["small"]
        taken_group = counters[key]["group"]
        out.append({
            "slot_iso": key,  # canonical local ISO hour string
            "available_small": max(0, CAPACITY["small"] - taken_small),
            "available_group": max(0, CAPACITY["group"] - taken_group),
        })

    return {
        "date": to_local_date_str(date_local),
        "slots": out,
        "capacity": CAPACITY,
    }


def get_today_availability() -> Dict[str, Any]:
    today_local = datetime.now(IST)
    return availability_for_date(today_local.strftime("%Y-%m-%d"))


def list_bookings_for_date(date_iso: str) -> Dict[str, Any]:
    """
    date_iso: 'YYYY-mm-dd' (local)
    """
    date_local = datetime.fromisoformat(date_iso).replace(tzinfo=IST)
    bookings = _load_bookings()
    same_day: List[Dict[str, Any]] = []
    for b in bookings:
        try:
            slot = parse_local_iso(b["slot_iso"])
        except Exception:
            continue
        if slot.date() == date_local.date():
            same_day.append(b)
    return {"date": to_local_date_str(date_local), "bookings": same_day}


# ----------------------------- capacity / booking --------------------------

def _has_capacity(table_type: str, slot_dt: datetime) -> bool:
    """
    Returns True if there is capacity for table_type at slot_dt (local hour bucket).
    """
    if table_type not in CAPACITY:
        return False
    bookings = _load_bookings()
    count = 0
    for b in bookings:
        if b.get("table_type") != table_type:
            continue
        try:
            b_slot = parse_local_iso(b["slot_iso"])
        except Exception:
            continue
        if _same_local_hour(b_slot, slot_dt):
            count += 1
    return count < CAPACITY[table_type]


def create_booking(
    name: str,
    email: str,
    table_type: str,
    seats: int,
    slot_iso: str,
    meal_preorder: List[str],
    note: str,
) -> Dict[str, Any]:
    """
    Create a booking if capacity allows; returns alternatives if full.
    """
    # Validate type + seat constraints
    if table_type not in ("small", "group"):
        return {"ok": False, "error": "invalid_table_type"}
    if table_type == "small" and seats > 2:
        return {"ok": False, "error": "small_table_max_2"}
    if table_type == "group" and seats > 5:
        return {"ok": False, "error": "group_table_max_5"}

    # Parse/normalize slot
    try:
        slot_dt = parse_local_iso(slot_iso)  # tz-aware local
    except Exception:
        return {"ok": False, "error": "invalid_slot_iso"}

    # Capacity check
    if not _has_capacity(table_type, slot_dt):
        # Propose nearby alternatives within ±2h (local hour buckets)
        alts = next_slots_nearby(slot_dt, hours=2)
        return {
            "ok": False,
            "error": "no_capacity",
            "alternatives": [s.astimezone(IST).replace(minute=0, second=0, microsecond=0).isoformat() for s in alts],
        }

    # Persist
    bookings = _load_bookings()
    booking = {
        "id": uuid.uuid4().hex,
        "name": name,
        "email": email,
        "table_type": table_type,
        "seats": int(seats),
        "slot_iso": slot_dt.astimezone(IST).replace(minute=0, second=0, microsecond=0).isoformat(),
        "meal_preorder": meal_preorder or [],
        "note": (note or "").strip(),
        "created_at": datetime.now(IST).isoformat(),
        # Optional: a dummy meeting link (spec said meet/dummy acceptable)
        "meet_link": f"https://meet.example.com/{uuid.uuid4().hex[:10]}"
    }
    bookings.append(booking)
    _save_bookings(bookings)

    # Email (non-fatal if fails)
    try:
        send_booking_confirmation({
            "name": booking["name"],
            "email": booking["email"],
            "table_type": booking["table_type"],
            "seats": booking["seats"],
            "slot_iso": booking["slot_iso"],
            "meal_preorder": booking["meal_preorder"],
            "note": booking["note"],
        })
    except Exception as e:
        # Keep booking success even if email fails
        print("[WARN] Booking created but email failed:", e)

    return {"ok": True, "booking": booking}
