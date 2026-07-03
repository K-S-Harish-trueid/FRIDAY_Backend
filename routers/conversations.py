from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from database import get_db
from models.db_models import Conversation, Message

router = APIRouter(prefix="/conversations", tags=["conversations"])


class ConversationOut(BaseModel):
    id: str
    title: str
    updated_at: datetime


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    timestamp: datetime


@router.post("/", response_model=ConversationOut)
async def create_conversation(db: AsyncSession = Depends(get_db)):
    conv = Conversation()
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return ConversationOut(id=str(conv.id), title=conv.title, updated_at=conv.updated_at)


@router.get("/", response_model=list[ConversationOut])
async def list_conversations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Conversation).order_by(Conversation.updated_at.desc()))
    convs = result.scalars().all()
    return [ConversationOut(id=str(c.id), title=c.title, updated_at=c.updated_at) for c in convs]


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def get_messages(conversation_id: UUID, db: AsyncSession = Depends(get_db)):
    conv = await db.get(Conversation, conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp)
    )
    msgs = result.scalars().all()
    return [
        MessageOut(id=str(m.id), role=m.role, content=m.content, timestamp=m.timestamp)
        for m in msgs
    ]


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: UUID, db: AsyncSession = Depends(get_db)):
    conv = await db.get(Conversation, conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conv)
    await db.commit()
    return {"deleted": str(conversation_id)}
