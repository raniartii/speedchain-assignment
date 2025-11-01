from fastapi import APIRouter
from pydantic import BaseModel
from backend.services.memory_service import memory

router = APIRouter()

class NewSessionResponse(BaseModel):
    session_id: str

@router.post("/new", response_model=NewSessionResponse)
def new_session():
    sid = memory.new_session()
    return NewSessionResponse(session_id=sid)

@router.post("/reset/{session_id}")
def reset_session(session_id: str):
    memory.reset_session(session_id)
    return {"ok": True}
