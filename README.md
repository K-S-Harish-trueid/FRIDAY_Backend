# F.R.I.D.A.Y Backend

FastAPI backend for the F.R.I.D.A.Y Flutter app.  
Current milestone: local command layer only — no external LLM calls yet.

---

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Copy the env template
cp .env.example .env   # then edit .env with real keys when needed
```

---

## Run

```bash
uvicorn main:app --reload
```

The server starts at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

---

## Endpoints

### `GET /health`
Basic health check.

```bash
curl http://localhost:8000/health
```

Response:
```json
{"status": "ok", "version": "0.1.0"}
```

---

### `POST /api/chat`
Send a message and get a response. Mirrors the shape `OwnService` in the Flutter app already sends and expects.

**Request body:**
```json
{
  "messages": [
    {"role": "user", "content": "what time is it"}
  ],
  "system": "optional system prompt string"
}
```

**Response:**
```json
{
  "response": "It's 14:32, boss."
}
```

**Example — time command:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "what time is it"}]}'
```

**Example — date command:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "what is today date"}]}'
```

**Example — unmatched (placeholder):**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "tell me about black holes"}]}'
```

Response:
```json
{
  "response": "No handler matched — external API integration not yet connected."
}
```

**Example — with conversation history:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "hello"},
      {"role": "assistant", "content": "Systems online. Ready when you are, boss."},
      {"role": "user", "content": "what time is it"}
    ]
  }'
```

---

## Project Structure

```
backend/
├── main.py                  # FastAPI app, middleware, router registration
├── config.py                # Settings via pydantic-settings (.env support)
├── .env.example             # Template for future API keys
├── requirements.txt
├── README.md
├── routers/
│   └── chat.py              # POST /api/chat  +  GET /health
├── services/
│   └── command_service.py   # Pluggable command handler registry
└── models/
    └── chat.py              # Pydantic request/response schemas
```

---

## Adding a New Command

Open [services/command_service.py](services/command_service.py) and add a handler function, then register it:

```python
def handle_weather(lower: str) -> Optional[CommandResult]:
    if _matches(lower, ["what's the weather", "weather today"]):
        # call weather_service here once wired up
        return CommandResult(response="Weather service not yet connected.", command_type="weather")
    return None

HANDLERS = [
    ...,
    handle_weather,   # <-- add here
]
```

---

## Adding a New External Service

1. Create `services/my_service.py` with an async function, e.g. `async def query(prompt: str) -> str`.
2. Add its env vars to `.env.example` and `config.py`.
3. Import and call it from `routers/chat.py` in the TODO block.

---

## Wiring into the Flutter App

The Flutter app's `OwnService` already calls `http://10.0.2.2:8000/chat` (Android emulator
localhost). This backend serves at `/api/chat`. When you're ready to wire it up, either:

- Update `ownApiUrl` in `lib/config.dart` to `http://10.0.2.2:8000/api/chat`, **or**
- Add a `/chat` alias route in `routers/chat.py` pointing to the same handler.
