from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi import HTTPException
from config import settings

_engine = None
_session_factory = None


def _get_engine():
    global _engine, _session_factory
    if _engine is None:
        if not settings.database_url:
            raise HTTPException(status_code=503, detail="DATABASE_URL is not configured.")
        _engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
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
