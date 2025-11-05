Here’s a **developer-style, realistic `README.md`** for your AI Café Receptionist project — written like something you’d actually find in a strong GitHub repo (not AI-fluff). It explains architecture, stack choices, setup, and usage in a concise, technical, human-written tone:

---

```markdown
# ☕ BrewHub Café – AI Receptionist

> Voice-driven café assistant built with **FastAPI**, **React**, and **LLM-powered workflow** that handles real-time conversation, table booking, and email confirmations.

---

## 🧠 Overview

BrewHub Café Assistant is an **end-to-end AI receptionist** that allows customers to talk naturally — the system listens, understands booking intent, remembers context, and replies back with natural speech.

### Core Flow
```

Voice → STT → LLM + FSM Memory → TTS → (Booking + Email) → JSON persistence

```

### Key Features
- 🎙️ **Voice-first chat** (STT + TTS pipeline)
- 🤖 **Context-aware conversation** using FSM memory
- 🗓️ **Table booking flow** (with validation & availability)
- 📧 **Professional confirmation email** with HTML template
- 🗃️ **Lightweight JSON-based persistence** (no external DB)

---

## ⚙️ Architecture

```

Frontend (React + Vite + Tailwind)
├── Recorder (voice capture)
├── Chat UI (conversation bubbles, typing effect)
└── Review UI (confirmation modal)

Backend (FastAPI)
├── STT Service      → Whisper / OpenAI
├── LLM Service      → GPT-4o-mini
├── Intent Service   → FSM for slot-filling
├── TTS Service      → ElevenLabs / gTTS
├── Booking Service  → Validation + Availability
├── Email Service    → SMTP + HTML templates
└── Memory Service   → Context tracking per session

Data (JSON)
├── bookings.json
├── conversations.json
└── openai.json / elevenlabs.json (keys)

Email API ↔ Backend (for confirmations)

````

> See `/docs/Architecture.png` for the full system diagram.

---

## 🧩 Tech Stack

| Layer | Tech | Purpose |
|-------|------|----------|
| **Frontend** | React, Vite, TailwindCSS | Modern UI with chat + recorder |
| **Backend** | FastAPI (Python) | API & business logic |
| **STT** | OpenAI Whisper | Speech → Text |
| **LLM** | GPT-4o-mini | Intent + dialogue logic |
| **FSM** | Custom Python state machine | Slot filling & context |
| **TTS** | ElevenLabs / gTTS | Text → Speech |
| **Storage** | JSON Files | Lightweight local persistence |
| **Email** | SMTP (smtplib) | Confirmation delivery |

---

## 🚀 Running Locally

### 1. Clone & Setup
```bash
git clone https://github.com/<your-username>/brewhub-ai-receptionist.git
cd brewhub-ai-receptionist/backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
````

### 2. Environment Keys

Store your API keys in `data/`:

**`data/openai.json`**

```json
{ "api_key": "sk-xxxx" }
```

**`data/elevenlabs.json`**

```json
{ "api_key": "elevenlabs-xxxx", "voice_id": "xxxx" }
```

### 3. Run the Backend

```bash
uvicorn main:app --reload --port 8000
```

### 4. Run the Frontend

```bash
cd ../frontend
npm install
npm run dev
```

Frontend runs at: [http://localhost:5173](http://localhost:5173)

---

## 💬 Conversation Logic

1. User sends **voice or text**
2. Backend transcribes via **STT**
3. **LLM + Intent Service** extracts slots:

   ```
   name, table_type, seats, slot_iso, email, meal, note
   ```
4. FSM memory tracks what’s filled → prompts the next missing field
5. Once all fields are captured, a **review modal** opens
6. On confirmation → `BookingService.create_booking()`:

   * Validates capacity
   * Writes to `bookings.json`
   * Triggers `EmailService` to send HTML confirmation
7. AI response is read back using **TTS**

---

## 🧱 Directory Structure

```
backend/
 ├── main.py
 ├── routes/
 │   ├── voice.py
 │   ├── bookings.py
 │   └── session.py
 ├── services/
 │   ├── llm_service.py
 │   ├── tts_service.py
 │   ├── transcribe_service.py
 │   ├── booking_service.py
 │   ├── intent_service.py
 │   ├── email_service.py
 │   └── memory_service.py
 ├── utils/
 │   ├── time_utils.py
 │   └── storage.py
 └── data/
     ├── bookings.json
     ├── conversations.json
     ├── openai.json
     └── elevenlabs.json

frontend/
 ├── src/
 │   ├── components/
 │   ├── api/
 │   ├── utils/
 │   └── App.jsx
 └── vite.config.js
```

---

## 📡 API Endpoints

| Method | Endpoint                | Description              |
| ------ | ----------------------- | ------------------------ |
| `POST` | `/api/voice/transcribe` | Audio → Text (STT)       |
| `POST` | `/api/voice/converse`   | Text → LLM → TTS reply   |
| `POST` | `/api/bookings/create`  | Create confirmed booking |
| `GET`  | `/api/bookings/today`   | Get today’s availability |
| `POST` | `/api/session/new`      | Create session memory    |

---

## 📧 Email Template Example

```html
<h2>BrewHub Café – Booking Confirmed</h2>
<p>Hi Uday,</p>
<p>Your booking details:</p>
<ul>
  <li><b>Date:</b> 2025-11-01T18:00:00+05:30</li>
  <li><b>Table:</b> Small (2-seater)</li>
  <li><b>Seats:</b> 2</li>
  <li><b>Meal Preorder:</b> None</li>
</ul>
<p>We look forward to seeing you! ☕</p>
<small>© BrewHub Café, 2025</small>
```

---

## 🧠 Model Choices

| Task      | Model            | Reason                             |
| --------- | ---------------- | ---------------------------------- |
| **STT**   | Whisper (OpenAI) | Fast & accurate transcription      |
| **LLM**   | GPT-4o-mini      | Cost-efficient + reasoning quality |
| **TTS**   | ElevenLabs       | Natural prosody & clarity          |
| **FSM**   | Custom logic     | Deterministic slot handling        |
| **Email** | SMTP             | Simple + portable                  |

---

---

## Demo

![alt text](<1.png>)
---
![alt text](<2.png>)
---
![alt text](<3.png>)
---
![alt text](<4.png>)
---

## 📈 Future Work

* Integrate **RAG** for dynamic menu queries
* Add **PostgreSQL** persistence
* Multi-lingual voice handling
* Frontend **WebSocket streaming**

---

## 🧑‍💻 Author

**Elspeth** – Software Developer
🔗 [GitHub](https://github.com/<your-username>) | [LinkedIn](https://linkedin.com/in/<your-profile>)

---

## License

MIT License © 2025 BrewHub Café

```

---

Would you like me to make this `README.md` also **include the architecture PNG** you generated (with an embedded image reference like `![Architecture](docs/Architecture.png)`)?  
It’ll look professional and presentation-ready on GitHub.
```
