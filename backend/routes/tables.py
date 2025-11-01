from fastapi import APIRouter
from backend.services.booking_service import availability_for_date

router = APIRouter()

@router.get("")
def availability(date_iso: str):
    return availability_for_date(date_iso)
