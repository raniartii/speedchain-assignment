from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from backend.services.booking_service import (
    get_today_availability,
    create_booking,
    list_bookings_for_date,
)

router = APIRouter()

class BookingIn(BaseModel):
    name: str
    email: EmailStr
    table_type: str  # "small"|"group"
    seats: int
    slot_iso: str    # ISO datetime string (local Asia/Kolkata date-time)
    meal_preorder: Optional[List[str]] = []
    note: Optional[str] = None

@router.get("/today")
def today():
    return get_today_availability()

@router.get("")
def list_for_date(date_iso: str):
    return list_bookings_for_date(date_iso)

@router.post("/create")
def create(b: BookingIn):
    r = create_booking(
        name=b.name,
        email=b.email,
        table_type=b.table_type,
        seats=b.seats,
        slot_iso=b.slot_iso,
        meal_preorder=b.meal_preorder or [],
        note=b.note or "",
    )
    if not r["ok"]:
        raise HTTPException(status_code=400, detail=r["error"])
    return r
