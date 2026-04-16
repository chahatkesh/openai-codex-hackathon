"""Standalone seed runner — can be called as `python -m scripts.seed_demo_tools`."""
import asyncio
from app.seed import run_seed

if __name__ == "__main__":
    asyncio.run(run_seed())
