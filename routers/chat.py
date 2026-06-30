from fastapi import APIRouter, HTTPException
from models.chat import ChatRequest, ChatResponse, HealthResponse
from services.command_service import dispatch
from services import openai_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", version="0.1.0")


@router.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    user_message = ""
    for msg in reversed(request.messages):
        if msg.role == "user":
            user_message = msg.content
            break

    # Step 1: local command layer (time, date, greetings, etc.)
    result = dispatch(user_message)
    if result is not None:
        return ChatResponse(response=result.response)

    # Step 2: fall through to OpenAI
    try:
        reply = openai_service.complete(request.messages)
        return ChatResponse(response=reply)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenAI error: {e}")
