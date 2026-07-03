from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.chat import router
from routers.conversations import router as conversations_router

app = FastAPI(
    title="F.R.I.D.A.Y Backend",
    description="Local command layer + LLM proxy with persistent conversation history.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(conversations_router)
