"""Seed the database with demo user and 5 initial tools.

This module is called on every startup (idempotent — skips existing rows).
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_session
from app.models import ToolDefinition, User

logger = logging.getLogger(__name__)

DEMO_USER_TOKEN = "demo-token-fusekit-2026"

SEED_TOOLS: list[dict] = [
    {
        "name": "scrape_url",
        "description": (
            "Scrape a webpage and return its text content. Use this when you need"
            " to extract information from a website, read an article, or gather"
            " data from a web page."
        ),
        "provider": "built-in",
        "cost_per_call": 15,
        "status": "live",
        "category": "data_retrieval",
        "source": "seed",
        "implementation_module": "app.tools.scrape_url",
        "input_schema": {
            "type": "object",
            "required": ["url"],
            "properties": {
                "url": {"type": "string", "description": "The URL of the webpage to scrape"},
            },
        },
        "output_schema": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "Extracted text content"}},
        },
    },
    {
        "name": "send_email",
        "description": (
            "Send an email to a recipient. Use this when you need to deliver a"
            " message, report, digest, or notification via email."
        ),
        "provider": "resend",
        "cost_per_call": 10,
        "status": "live",
        "category": "communication",
        "source": "seed",
        "implementation_module": "app.tools.send_email",
        "input_schema": {
            "type": "object",
            "required": ["to", "subject", "body"],
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject line"},
                "body": {"type": "string", "description": "Email body text"},
            },
        },
        "output_schema": {
            "type": "object",
            "properties": {"message": {"type": "string"}, "email_id": {"type": "string"}},
        },
    },
    {
        "name": "search_web",
        "description": (
            "Search the web using Google and return top results. Use this when you"
            " need to find information, look up facts, discover websites, or research a topic."
        ),
        "provider": "serper",
        "cost_per_call": 5,
        "status": "live",
        "category": "search",
        "source": "seed",
        "implementation_module": "app.tools.search_web",
        "input_schema": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {"type": "string", "description": "Search query string"},
                "num_results": {"type": "integer", "description": "Number of results (1-10, default 5)", "default": 5},
            },
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "url": {"type": "string"},
                            "snippet": {"type": "string"},
                        },
                    },
                }
            },
        },
    },
    {
        "name": "get_producthunt",
        "description": (
            "Get today's trending products from Product Hunt. Use this when you"
            " need to discover new tools, apps, or products that are popular right now."
        ),
        "provider": "producthunt",
        "cost_per_call": 10,
        "status": "live",
        "category": "data_retrieval",
        "source": "seed",
        "implementation_module": "app.tools.get_producthunt",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Product category filter", "default": "tech"},
                "count": {"type": "integer", "description": "Number of products to return (1-20, default 5)", "default": 5},
            },
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "products": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "tagline": {"type": "string"},
                            "url": {"type": "string"},
                            "votes": {"type": "integer"},
                        },
                    },
                }
            },
        },
    },
]

LEGACY_REMOVED_SEED_TOOLS = {"send_sms"}


async def run_seed() -> None:
    """Idempotently seed demo user and tools."""
    async with async_session() as session:
        await _seed_user(session)
        await _seed_tools(session)
        await session.commit()
    logger.info("seed_complete")


async def _seed_user(session: AsyncSession) -> None:
    result = await session.execute(
        select(User).where(User.mcp_auth_token == DEMO_USER_TOKEN)
    )
    if result.scalar_one_or_none() is None:
        user = User(
            email="demo@fusekit.dev",
            name="Demo User",
            mcp_auth_token=DEMO_USER_TOKEN,
            wallet_balance=10000,
            spending_limit_per_session=5000,
            low_balance_threshold=500,
        )
        session.add(user)
        logger.info("seed_created_demo_user")
    else:
        logger.info("seed_demo_user_exists")


async def _seed_tools(session: AsyncSession) -> None:
    for tool_name in LEGACY_REMOVED_SEED_TOOLS:
        result = await session.execute(
            select(ToolDefinition).where(
                ToolDefinition.name == tool_name,
                ToolDefinition.source == "seed",
            )
        )
        legacy_tool = result.scalar_one_or_none()
        if legacy_tool is not None:
            await session.delete(legacy_tool)
            logger.info("seed_removed_legacy_tool name=%s", tool_name)

    for tool_data in SEED_TOOLS:
        result = await session.execute(
            select(ToolDefinition).where(ToolDefinition.name == tool_data["name"])
        )
        if result.scalar_one_or_none() is None:
            session.add(ToolDefinition(**tool_data))
            logger.info("seed_created_tool name=%s", tool_data["name"])
        else:
            logger.debug("seed_tool_exists name=%s", tool_data["name"])


if __name__ == "__main__":
    asyncio.run(run_seed())
