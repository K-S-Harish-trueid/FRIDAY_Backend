# F.R.I.D.A.Y Backend

FastAPI backend for the F.R.I.D.A.Y Flutter app — the **only** place LLM calls
happen. The Flutter client never talks to Groq/Gemini directly; it only ever
calls this API.

**Architecture:**
- **Groq** (`llama-3.3-70b-versatile`) is the primary LLM.
- **Gemini** (`gemini-2.0-flash`) is the automatic fallback if the Groq call fails.
- **Supabase Postgres** (SQLAlchemy async + asyncpg) persists conversations and messages.
- **Local commands** (time, date, greetings, jokes, etc.) are handled entirely
  client-side in the Flutter app — the backend has no command layer of its own.
- **Tool calling** (weather, web search, maps, location) — coming soon via Groq's
  native function-calling API.

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
Send a message and get an LLM-generated response, persisted to the conversation.

**Request body:**
```json
{
  "messages": [
    {"role": "user", "content": "Who built you?"}
  ],
  "conversation_id": "optional existing conversation UUID"
}
```

**Response:**
```json
{
  "response": "Built by Harish, boss. Systems nominal.",
  "conversation_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

- Omit `conversation_id` to start a new conversation (one is created and returned).
- Pass a known `conversation_id` back in to continue that conversation; an unknown id returns `404`.
- If the Groq call fails, the backend automatically retries with Gemini before
  returning a `502`.

**Example:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Who built you?"}]}'
```

**Example — continuing a conversation:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Who built you?"},
      {"role": "assistant", "content": "Built by Harish, boss."},
      {"role": "user", "content": "Tell me a fun fact."}
    ],
    "conversation_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
  }'
```

### Conversation history

- `POST /conversations/` — create an empty conversation
- `GET /conversations/` — list conversations, newest first
- `GET /conversations/{id}/messages` — fetch all messages in a conversation
- `DELETE /conversations/{id}` — delete a conversation and its messages

---

## Project Structure

```
backend/
├── main.py                  # FastAPI app, middleware, router registration
├── config.py                # Settings via pydantic-settings (.env support)
├── database.py               # Async SQLAlchemy engine/session setup
├── .env.example              # Template for API keys / DB URL
├── requirements.txt
├── README.md
├── routers/
│   ├── chat.py               # POST /api/chat  +  GET /health
│   └── conversations.py      # Conversation history endpoints
├── services/
│   ├── groq_service.py       # Primary LLM (Groq, llama-3.3-70b-versatile)
│   └── gemini_service.py     # Fallback LLM (Gemini, gemini-2.0-flash)
└── models/
    ├── chat.py                # Pydantic request/response schemas
    └── db_models.py           # SQLAlchemy Conversation / Message tables
```

---

## Adding a New External Service

1. Create `services/my_service.py` with an async function, e.g. `async def query(prompt: str) -> str`.
2. Add its env vars to `.env.example` and `config.py`.
3. Import and call it from `routers/chat.py`.

---

## Roadmap

Tool calling (Groq native function calling) is next: `get_weather` (Open-Meteo),
`web_search` (DuckDuckGo), `get_current_location` and `open_maps` (device
actions handed back to the Flutter client). See `services/tool_service.py`
once added.
