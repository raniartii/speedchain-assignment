import base64
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from backend.services import transcribe_service
from backend.services import tts_service
from backend.services.intent_service import interpret_text_and_update_session
from backend.services.memory_service import memory

router = APIRouter()

class ConverseIn(BaseModel):
    session_id: str
    user_text: str

class ConverseOut(BaseModel):
    session_id: str
    reply_text: str
    tts_audio_base64: str
    state: dict
    last_intent: str

@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    try:
        data = await file.read()
        r = transcribe_service.transcribe_audio_bytes(data, filename_hint=file.filename or "audio.webm")
        if not r.get("ok"):
            raise HTTPException(status_code=400, detail=r.get("error", "transcription_failed"))
        return {"ok": True, "text": r["text"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"transcription_error: {e}")

@router.post("/converse", response_model=ConverseOut)
def converse(payload: ConverseIn):
    sid = payload.session_id
    if not memory.exists(sid):
        sid = memory.new_session()

    result = interpret_text_and_update_session(session_id=sid, user_text=payload.user_text)

    # TTS
    tts = tts_service.text_to_speech_base64(result["reply_text"])
    if not tts.get("ok"):
        # return silent audio if TTS fails, but don't crash the flow
        audio_b64 = ""
    else:
        audio_b64 = tts["audio_base64"]

    return ConverseOut(
        session_id=sid,
        reply_text=result["reply_text"],
        tts_audio_base64=audio_b64,
        state=result["state"],
        last_intent=result["last_intent"],
    )
