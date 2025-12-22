from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.voice import router as voice_router
from backend.routes.bookings import router as bookings_router
from backend.routes.tables import router as tables_router
from backend.routes.session import router as session_router

app = FastAPI(title="BrewHub Café – AI Receptionist", version="1.0.0")

@app.on_event("startup")
async def warmup():
    try:
        from backend.services.stt_service import _get_whisper_model
        _get_whisper_model()
    except Exception:
        pass


# CORS – adjust frontend origin if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session_router, prefix="/api/session", tags=["session"])
app.include_router(voice_router, prefix="/api/voice", tags=["voice"])
app.include_router(bookings_router, prefix="/api/bookings", tags=["bookings"])
app.include_router(tables_router, prefix="/api/tables", tags=["tables"])

@app.get("/api/health")
def health():
    return {"ok": True, "service": "ai-receptionist", "version": "1.0.0"}

@app.get("/")
def root():
    return {"message": "Backend is running"}


