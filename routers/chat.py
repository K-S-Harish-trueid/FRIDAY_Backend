from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.chat import ChatRequest, ChatResponse, HealthResponse
from models.db_models import Conversation, Message
from services import groq_service, gemini_service

router = APIRouter()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="0.2.0")


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    user_message = ""
    for msg in reversed(request.messages):
        if msg.role == "user":
            user_message = msg.content
            break

    # Validate conversation_id first — before the LLM call so an invalid ID
    # always returns 404 regardless of message content.
    conv = None
    if request.conversation_id is not None:
        conv = await db.get(Conversation, request.conversation_id)
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # Get or create conversation
    if conv is None:
        conv = Conversation(title=user_message[:40].strip() or "New Conversation")
        db.add(conv)
        await db.flush()

    # Persist user message
    db.add(Message(conversation_id=conv.id, role="user", content=user_message))

    # Groq primary, Gemini fallback
    try:
        reply = await groq_service.complete(request.messages)
    except Exception as groq_error:
        try:
            reply = await gemini_service.complete(request.messages)
        except Exception as gemini_error:
            await db.rollback()
            raise HTTPException(
                status_code=502,
                detail=f"Groq error: {groq_error}; Gemini error: {gemini_error}",
            )

    # Persist assistant reply and bump updated_at
    db.add(Message(conversation_id=conv.id, role="assistant", content=reply))
    conv.updated_at = _utcnow()

    await db.commit()

    return ChatResponse(response=reply, conversation_id=str(conv.id))
