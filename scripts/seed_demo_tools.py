"""Seed the database with demo user and 5 initial tools."""

import asyncio

from sqlalchemy import select

from app.db import async_session
from app.models import ToolDefinition, User
from app.mcp_server import DEMO_USER_TOKEN


SEED_TOOLS = [
    {
        "name": "scrape_url",
        "description": "Scrape a webpage and return its text content. Use this when you need to extract information from a website, read an article, or gather data from a web page.",
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
                "url": {
                    "type": "string",
                    "description": "The URL of the webpage to scrape",
                }
            },
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Extracted text content"}
            },
        },
    },
    {
        "name": "send_email",
        "description": "Send an email to a recipient. Use this when you need to deliver a message, report, digest, or notification via email.",
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
                "to": {
                    "type": "string",
                    "description": "Recipient email address",
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line",
                },
                "body": {
                    "type": "string",
                    "description": "Email body text",
                },
            },
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "email_id": {"type": "string"},
            },
        },
    },
    {
        "name": "send_sms",
        "description": "Send an SMS text message to a phone number. Use this when you need to send a text notification, alert, or short message to someone's phone.",
        "provider": "twilio",
        "cost_per_call": 20,
        "status": "live",
        "category": "communication",
        "source": "seed",
        "implementation_module": "app.tools.send_sms",
        "input_schema": {
            "type": "object",
            "required": ["to", "message"],
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient phone number in E.164 format (e.g., +1234567890)",
                },
                "message": {
                    "type": "string",
                    "description": "SMS message body (max 1600 chars)",
                },
            },
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "sid": {"type": "string"},
            },
        },
    },
    {
        "name": "search_web",
        "description": "Search the web using Google and return top results. Use this when you need to find information, look up facts, discover websites, or research a topic.",
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
                "query": {
                    "type": "string",
                    "description": "Search query string",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-10, default 5)",
                    "default": 5,
                },
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
        "description": "Get today's trending products from Product Hunt. Use this when you need to discover new tools, apps, or products that are popular right now.",
        "provider": "producthunt",
        "cost_per_call": 10,
        "status": "live",
        "category": "data_retrieval",
        "source": "seed",
        "implementation_module": "app.tools.get_producthunt",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Product category filter (default: 'tech')",
                    "default": "tech",
                },
                "count": {
                    "type": "integer",
                    "description": "Number of products to return (1-20, default 5)",
                    "default": 5,
                },
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


async def seed():
    async with async_session() as session:
        # Create demo user if not exists
        existing = await session.execute(
            select(User).where(User.mcp_auth_token == DEMO_USER_TOKEN)
        )
        if existing.scalar_one_or_none() is None:
            user = User(
                email="demo@fusekit.dev",
                name="Demo User",
                mcp_auth_token=DEMO_USER_TOKEN,
                wallet_balance=10000,
                spending_limit_per_session=5000,
                low_balance_threshold=500,
            )
            session.add(user)
            print("Created demo user (demo@fusekit.dev, 10000 credits)")
        else:
            print("Demo user already exists")

        # Seed tools
        for tool_data in SEED_TOOLS:
            existing_tool = await session.execute(
                select(ToolDefinition).where(ToolDefinition.name == tool_data["name"])
            )
            if existing_tool.scalar_one_or_none() is None:
                tool = ToolDefinition(**tool_data)
                session.add(tool)
                print(f"Seeded tool: {tool_data['name']}")
            else:
                print(f"ℹTool already exists: {tool_data['name']}")

        await session.commit()

    print("\nSeed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
