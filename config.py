from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Server ────────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000

    # ── LLM keys ──────────────────────────────────────────────────────────────
    groq_api_key: str = ""
    # groq_api_key: str = ""
    # gemini_api_key: str = ""
    # anthropic_api_key: str = ""

    # ── Future external API base URLs ─────────────────────────────────────────
    # pokeapi_base_url: str = "https://pokeapi.co/api/v2"
    # openweather_base_url: str = "https://api.openweathermap.org/data/2.5"
    # openweather_api_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
