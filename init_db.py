import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from models.db_models import Base
from config import settings


async def init():
    if not settings.database_url:
        print("ERROR: DATABASE_URL is not set in .env")
        return
    engine = create_async_engine(settings.database_url, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("\nTables created successfully.")


if __name__ == "__main__":
    asyncio.run(init())
