from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.chat import router

app = FastAPI(
    title="F.R.I.D.A.Y Backend",
    description="Local command layer + future LLM proxy for the F.R.I.D.A.Y Flutter app.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# TODO: register additional routers here as services are added, e.g.:
#   from routers.pokemon import router as pokemon_router
#   app.include_router(pokemon_router, prefix="/api")
