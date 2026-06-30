from fastapi import APIRouter
from models.chat import ChatRequest, ChatResponse, HealthResponse
from services.command_service import dispatch

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", version="0.1.0")


@router.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # Extract the latest user message (last entry with role == "user")
    user_message = ""
    for msg in reversed(request.messages):
        if msg.role == "user":
            user_message = msg.content
            break

    # Step 1: local command layer
    result = dispatch(user_message)
    if result is not None:
        return ChatResponse(response=result.response)

    # TODO: intent-based API routing goes here, e.g.:
    #   if intent == "pokemon": return pokeapi_service.query(user_message)
    #   if intent == "chat":    return chatgpt_service.complete(request.messages)

    return ChatResponse(
        response="No handler matched — external API integration not yet connected."
    )
