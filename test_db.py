"""
Run with: python test_db.py
Tests DB connection and table creation independently of the API server.
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config import settings

GREEN = "\033[92m"
RED   = "\033[91m"
CYAN  = "\033[96m"
BOLD  = "\033[1m"
RESET = "\033[0m"


async def main():
    if sys.platform == "win32":
        import os; os.system("")

    print(f"\n{CYAN}{BOLD}F.R.I.D.A.Y — DB Connection Test{RESET}\n")

    if not settings.database_url:
        print(f"{RED}✗ DATABASE_URL is not set in .env{RESET}")
        sys.exit(1)

    if "[password]" in settings.database_url:
        print(f"{RED}✗ DATABASE_URL still has the placeholder [password].{RESET}")
        print("  Edit .env and replace [password] with your real Supabase password.")
        sys.exit(1)

    print(f"  URL: {settings.database_url[:60]}...")
    print(f"  Connecting...\n")

    engine = create_async_engine(settings.database_url, echo=False)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"{GREEN}✓ Connected!{RESET}")
            print(f"  {version}\n")

        # Create tables
        from models.db_models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print(f"{GREEN}✓ Tables created (or already exist){RESET}\n")

    except Exception as e:
        print(f"{RED}✗ Connection failed:{RESET}")
        print(f"  {e}\n")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
