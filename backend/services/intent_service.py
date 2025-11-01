from __future__ import annotations
import re
from typing import Dict, Any, List
from backend.services.llm_service import chat_with_llm
from backend.services.booking_service import create_booking
from backend.services.memory_service import memory
from backend.utils.time_utils import parse_user_time_to_local_slot, normalize_table_type

RE_EMAIL = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
RE_NAME_PHRASE = re.compile(r"\b(?:my\s+name\s+is|i\s*am|i'm|this\s+is|name\s*[:\-]?)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)", re.I)
RE_JUST_NAME = re.compile(r"^\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s*$")
RE_SMALL = re.compile(r"\b(?:small|2|two|two[-\s]?seater|couple|pair)\b", re.I)
RE_GROUP = re.compile(r"\b(?:group|5|five|five[-\s]?seater|team)\b", re.I)
RE_SEATS = re.compile(r"\b(\d+)\s*(?:people|persons|seats?)\b", re.I)
RE_YES = re.compile(r"\b(yes|yep|yeah|confirm|book it|go ahead|please book)\b", re.I)
RE_NO = re.compile(r"\b(no|nope|wait|change|edit)\b", re.I)
RE_SKIP = re.compile(r"\b(skip|none|no thanks|no thank you|not now)\b", re.I)
RE_MEAL = re.compile(r"\b(coffee|sandwich|pastry|lunch combo|lunch|tea)\b", re.I)

RE_SMALLTALK = re.compile(r"\b(hi|hello|hey|good\s+(morning|afternoon|evening))\b", re.I)

FIELDS_ORDER = ["name", "table_type", "seats", "slot_iso", "email"]  # booking-required

def _extract_name(text: str) -> str | None:
    m = RE_NAME_PHRASE.search(text)
    if m: return m.group(1)
    m2 = RE_JUST_NAME.search(text.strip())
    if m2 and len(text.split()) <= 3: return m2.group(1)
    return None

def _extract_email(text: str) -> str | None:
    m = RE_EMAIL.search(text)
    return m.group(0) if m else None

def _extract_table_type(text: str) -> str | None:
    if RE_GROUP.search(text): return "group"
    if RE_SMALL.search(text): return "small"
    return None

def _extract_seats(text: str, fallback_type: str | None) -> int | None:
    m = RE_SEATS.search(text)
    if m:
        try: return int(m.group(1))
        except Exception: pass
    if fallback_type == "small": return 2
    if fallback_type == "group": return 5
    return None

def _extract_meal(text: str) -> List[str]:
    out = []
    for m in RE_MEAL.finditer(text):
        v = m.group(1).lower()
        if v == "lunch": v = "lunch combo"
        out.append(v.title())
    # unique order-preserving
    seen=set(); uniq=[]
    for v in out:
        if v not in seen:
            uniq.append(v); seen.add(v)
    return uniq

def _missing_required(slots: Dict[str, Any]) -> List[str]:
    miss=[]
    if not slots.get("name"): miss.append("name")
    if not slots.get("table_type"): miss.append("table_type")
    if not slots.get("seats"): miss.append("seats")
    if not slots.get("slot_iso"): miss.append("slot_iso")
    if not slots.get("email"): miss.append("email")
    return miss

def _next_required(slots: Dict[str, Any]) -> str | None:
    miss=_missing_required(slots)
    for f in FIELDS_ORDER:
        if f in miss: return f
    return None

def _ask_for(field: str, slots: Dict[str, Any]) -> str:
    nm = slots.get("name")
    if field == "name": return "Welcome to BrewHub! What’s your name?"
    if field == "table_type": return f"Nice to meet you{(' ' + nm) if nm else ''}. Do you want a small (2-seater) or a group (5-seater) table?"
    if field == "seats":
        tt = slots.get("table_type")
        if tt == "small": return "How many seats do you need? (up to 2 for a small table)"
        if tt == "group": return "How many seats do you need? (up to 5 for a group table)"
        return "How many seats do you need?"
    if field == "slot_iso": return "What time works for you? e.g., “today 5 pm” or “tomorrow 17:00”."
    if field == "email": return "Lastly, what’s your email for the confirmation?"
    return "Tell me the next detail."

def _summary_line(slots: Dict[str, Any]) -> str:
    nm = slots.get("name") or "guest"
    tt = slots.get("table_type") or "small"
    seats = slots.get("seats") or (2 if tt=="small" else 5)
    when = slots.get("slot_iso") or "—"
    meal = slots.get("meal") or []
    note = (slots.get("note") or "").strip()
    parts = [f"A {tt} table for {seats} at {when}."]
    if meal: parts.append(f"Pre-order: {', '.join(meal)}.")
    if note: parts.append(f"Note: {note}.")
    return f"Okay {nm}. " + " ".join(parts)

def _ack(slots: Dict[str, Any]) -> str:
    nm = slots.get("name")
    return f"Thanks, {nm}." if nm else "Got it."

def interpret_text_and_update_session(session_id: str, user_text: str) -> Dict[str, Any]:
    state = memory.get(session_id)
    memory.append_turn(session_id, "user", user_text)
    slots = state["slots"]

    # Extract core + optional on every turn
    nm = _extract_name(user_text)
    if nm: slots["name"] = nm

    email = _extract_email(user_text)
    if email: slots["email"] = email

    tt = _extract_table_type(user_text)
    if tt: slots["table_type"] = normalize_table_type(tt)

    seats = _extract_seats(user_text, slots.get("table_type"))
    if seats: slots["seats"] = seats

    slot_iso = parse_user_time_to_local_slot(user_text)
    if slot_iso: slots["slot_iso"] = slot_iso

    # Optional meal parse unless user says skip
    if RE_SKIP.search(user_text):
        # if we were on optional steps, mark them done respectfully
        if not state.get("asked_meal"): state["asked_meal"] = True
        elif not state.get("asked_note"): state["asked_note"] = True
    else:
        meals = _extract_meal(user_text)
        if meals:
            slots["meal"] = meals

        # For note: if user writes a sentence without being an email or command, accept as note
        cleaned = user_text.strip()
        if (not RE_EMAIL.search(cleaned)) and len(cleaned.split()) >= 3:
            # Heuristic: avoid overwriting when they're answering required fields
            if not _next_required(slots):
                slots["note"] = cleaned

    # Confirmation branch
    if state.get("awaiting_confirmation"):
        if RE_NO.search(user_text):
            state["awaiting_confirmation"] = False
            reply = "No problem. What would you like to change—table type, seats, time, meal, note, or email?"
            state["last_intent"] = "edit_before_confirm"
        elif RE_YES.search(user_text):
            bres = create_booking(
                name=slots["name"],
                email=slots["email"],
                table_type=slots["table_type"],
                seats=int(slots["seats"]),
                slot_iso=slots["slot_iso"],
                meal_preorder=slots.get("meal") or [],
                note=slots.get("note") or ""
            )
            if bres.get("ok"):
                b = bres["booking"]
                reply = (f"Booked ✅ {b['table_type']} table for {b['seats']} at {b['slot_iso']} "
                         f"for {b['name']}. I’ve emailed the confirmation to {b['email']}.")
                state["awaiting_confirmation"] = False
                state["last_intent"] = "booked"
            else:
                if bres.get("alternatives"):
                    alts = "; ".join(bres["alternatives"])
                    reply = f"That slot is full. Nearby options: {alts}. Which one should I pick?"
                else:
                    reply = f"Couldn't book: {bres.get('error','unknown_error')}."
                state["last_intent"] = "booking_failed"
        else:
            reply = "Please say ‘yes’ to confirm or ‘no’ to edit."
            state["last_intent"] = "awaiting_confirmation"

        memory.persist_snapshot(session_id)
        memory.append_turn(session_id, "assistant", reply)
        return {"reply_text": reply, "state": state, "last_intent": state["last_intent"]}

    # Required fields gating
    need = _next_required(slots)
    if need:
        if RE_SMALLTALK.search(user_text):
            reply = f"Hi! {_ask_for(need, slots)}"
        else:
            reply = f"{_ack(slots)} {_ask_for(need, slots)}"
        state["last_intent"] = f"ask_{need}"
        memory.persist_snapshot(session_id)
        memory.append_turn(session_id, "assistant", reply)
        return {"reply_text": reply, "state": state, "last_intent": state["last_intent"]}

    # Optional step 1: Meal (ask once)
    if not state.get("asked_meal"):
        state["asked_meal"] = True
        reply = ("Would you like to pre-order anything? Options: Coffee, Sandwich, Pastry, Lunch Combo, Tea. "
                 "Say ‘skip’ if you don’t want to add a meal.")
        state["last_intent"] = "ask_meal"
        memory.persist_snapshot(session_id)
        memory.append_turn(session_id, "assistant", reply)
        return {"reply_text": reply, "state": state, "last_intent": state["last_intent"]}

    # Optional step 2: Note (ask once)
    if not state.get("asked_note"):
        state["asked_note"] = True
        reply = "Any note for this booking (e.g., company name, occasion, quiet corner)? You can say ‘skip’."
        state["last_intent"] = "ask_note"
        memory.persist_snapshot(session_id)
        memory.append_turn(session_id, "assistant", reply)
        return {"reply_text": reply, "state": state, "last_intent": state["last_intent"]}

    # All done → summarize + confirm
    summary = _summary_line(slots)
    reply = f"{summary} Shall I confirm the booking now? (yes/no)"
    state["awaiting_confirmation"] = True
    state["last_intent"] = "summarize_and_confirm"
    memory.persist_snapshot(session_id)
    memory.append_turn(session_id, "assistant", reply)
    return {"reply_text": reply, "state": state, "last_intent": state["last_intent"]}
