"""Simple scraper tester for the FuseKit platform tool.

Usage:
    source .venv/bin/activate
    PYTHONPATH=services/platform python scripts/test_scraper.py https://docs.stripe.com/api

Optional flags:
    --raw    Print the full JSON response
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from app.tools.scrape_url import execute


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Test the FuseKit scrape_url tool against a URL.")
    parser.add_argument("url", help="Docs or webpage URL to scrape")
    parser.add_argument("--raw", action="store_true", help="Print the full JSON payload")
    return parser


def print_summary(payload: dict) -> None:
    print(f"URL: {payload.get('url', '-')}")
    print(f"Type: {payload.get('content_type', '-')}")
    print(f"Title: {payload.get('title', '-')}")

    summary = payload.get("summary")
    if summary:
        print(f"Summary: {summary}")

    headings = payload.get("headings") or []
    if headings:
        print("\nHeadings:")
        for item in headings[:8]:
            print(f"- {item}")

    auth_hints = payload.get("auth_hints") or []
    if auth_hints:
        print("\nAuth hints:")
        for item in auth_hints[:5]:
            print(f"- {item}")

    endpoint_hints = payload.get("endpoint_hints") or []
    if endpoint_hints:
        print("\nEndpoint hints:")
        for item in endpoint_hints[:8]:
            print(f"- {item}")

    code_blocks = payload.get("code_blocks") or []
    if code_blocks:
        print("\nFirst code block:")
        print(code_blocks[0][:1200])

    text = payload.get("text") or ""
    if text:
        print("\nText preview:")
        print(text[:1500])

    metadata = payload.get("metadata") or {}
    if metadata:
        print("\nMetadata:")
        for key, value in metadata.items():
            print(f"- {key}: {value}")


async def main() -> int:
    args = build_parser().parse_args()
    raw = await execute(args.url)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        print(raw)
        return 0

    if args.raw:
        print(json.dumps(payload, indent=2))
    else:
        print_summary(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
