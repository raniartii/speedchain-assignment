"""
Volatile in-process memory for sessions + persistent append to data/conversations.json
No DB usage.
"""
import uuid
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CONV_FILE = DATA_DIR / "conversations.json"

class MemoryStore:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def new_session(self) -> str:
        sid = uuid.uuid4().hex
        self.sessions[sid] = {
            "slots": {
                "name": None,
                "email": None,
                "table_type": None,   # "small"|"group"
                "seats": None,
                "slot_iso": None,     # local ISO
                "meal": [],
                "note": ""
            },
            "awaiting_confirmation": False,
            "asked_meal": False,      # <-- NEW
            "asked_note": False,      # <-- NEW
            "transcript": [],
            "last_intent": "unknown"
        }
        return sid

    def reset_session(self, sid: str):
        if sid in self.sessions:
            self.sessions.pop(sid, None)

    def exists(self, sid: str) -> bool:
        return sid in self.sessions

    def get(self, sid: str) -> Dict[str, Any]:
        return self.sessions[sid]

    def append_turn(self, sid: str, speaker: str, text: str):
        self.sessions[sid]["transcript"].append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "speaker": speaker,
            "text": text
        })

    def get_recent_transcript(self, sid: str, n: int = 8) -> List[Dict[str, Any]]:
        tr = self.sessions.get(sid, {}).get("transcript", [])
        if n <= 0: return []
        return tr[-n:]

    def persist_snapshot(self, sid: str):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "session_id": sid,
            "ts": datetime.now(timezone.utc).isoformat(),
            "state": self.sessions.get(sid, {})
        }
        try:
            with (DATA_DIR / "conversations.json").open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:
            pass

memory = MemoryStore()
