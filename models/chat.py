from pydantic import BaseModel
from typing import Optional


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    system: Optional[str] = None


class ChatResponse(BaseModel):
    # Matches what OwnService in the Flutter app expects: data['response']
    response: str


class HealthResponse(BaseModel):
    status: str
    version: str
