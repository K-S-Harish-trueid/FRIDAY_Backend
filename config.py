from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Server ────────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000

    # ── LLM keys ──────────────────────────────────────────────────────────────
    groq_api_key: str = ""

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = ""  # must come from env — no secrets hardcoded here

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()