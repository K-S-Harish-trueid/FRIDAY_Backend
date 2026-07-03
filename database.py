from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi import HTTPException
from config import settings

_engine = None
_session_factory = None


def _normalize_db_url(url: str) -> str:
    """Force the asyncpg driver regardless of how the URL was pasted in."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        # Some providers hand out the short 'postgres://' scheme,
        # which SQLAlchemy doesn't recognize at all.
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


def _get_engine():
    global _engine, _session_factory
    if _engine is None:
        if not settings.database_url:
            raise HTTPException(status_code=503, detail="DATABASE_URL is not configured.")

        db_url = _normalize_db_url(settings.database_url)

        # Debug: log driver + host only, never the password.
        scheme = db_url.split("://")[0]
        host_part = db_url.split("@")[-1] if "@" in db_url else "(no host found)"
        print(f"[DB] driver={scheme} host={host_part}")

        _engine = create_async_engine(db_url, echo=False, pool_pre_ping=True)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)
    return _engine, _session_factory


async def get_db():
    _, session_factory = _get_engine()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise