"""DB initialisation entrypoint — run as `python -m app.db_init` from services/platform.

Waits for PostgreSQL to be ready, creates tables, then seeds demo data.
Safe to run multiple times (idempotent).
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure repo-root scripts/ is importable when running from services/platform
# Path to this file: services/platform/app/db_init.py
# Parents: app (0), platform (1), services (2), fusekit (3)
repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(repo_root))

try:
    from app.seed import run_seed as seed
except ImportError as e:
    print(f"  Warning: Could not import seed script: {e}")
    print(f"  Repo root detected as: {repo_root}")
    print(f"  Seed will be skipped.")

    async def seed():  # noqa: F811
        pass


async def wait_for_db(max_retries: int = 20, delay: float = 2.0) -> None:
    """Wait until PostgreSQL accepts connections."""
    from app.db import engine

    for attempt in range(1, max_retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            print(f"  ✓ PostgreSQL ready (attempt {attempt})")
            return
        except Exception:
            print(f"  ⏳ Waiting for PostgreSQL... ({attempt}/{max_retries})")
            await asyncio.sleep(delay)

    print("  ✗ Could not connect to PostgreSQL after retries. Skipping seed.")
    raise SystemExit(1)


async def create_tables() -> None:
    """Create all tables if they don't exist."""
    from app.db import engine
    from app.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  ✓ Database tables ensured")


async def main() -> None:
    await wait_for_db()
    await create_tables()
    await seed()


if __name__ == "__main__":
    asyncio.run(main())
