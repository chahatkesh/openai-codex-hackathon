<img width="3000" height="1000" alt="Git Repo Cover" src="https://github.com/user-attachments/assets/8ddae07c-14ee-4664-9711-5e06effcc5ef" />

# FuseKit

> A self-growing API marketplace for Codex.

[![Built for OpenAI Codex Hackathon](https://img.shields.io/badge/OpenAI%20Codex-Hackathon%202026-412991)](https://openai.com)
[![MCP](https://img.shields.io/badge/MCP-enabled-111827)](https://modelcontextprotocol.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-platform-009688)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-dashboard-black)](https://nextjs.org)

## What Is FuseKit?

FuseKit gives Codex one place to discover, call, pay for, and grow API tools.

Instead of asking developers to manually find API docs, write wrappers, handle credentials, and wire billing, FuseKit exposes a marketplace of callable tools through MCP. Codex can ask FuseKit what tools exist, call the tools it needs, and request a new integration when something is missing.

The simple idea:

```text
Codex needs a capability
        |
        v
FuseKit checks the catalog
        |
        |-- tool exists --> wallet check --> execute API --> return result
        |
        `-- tool missing --> Codex-powered integration pipeline --> publish new tool
```

## What It Does

- Gives Codex an MCP server with `tools/list` and `tools/call`.
- Runs useful tools such as `scrape_url`, `send_email`, `send_sms`, `search_web`, and `get_producthunt`.
- Checks wallet balance before every paid tool call.
- Logs execution and billing in the platform backend.
- Returns clear errors such as `TOOL_NOT_FOUND` and `INSUFFICIENT_FUNDS`.
- Turns missing tools into integration jobs.
- Uses a bounded pipeline to discover docs, read API details, generate code, test/fix it, and publish the new tool.
- Shows the catalog, wallet, credentials, integration jobs, and live feed in a Next.js dashboard.

## How We Used Codex

Codex was not just a helper for small code edits. We used Codex as the engineering partner for the whole project.

Codex helped us:

- Understand and reshape the project into a split architecture.
- Build the FastAPI platform service for MCP, wallet checks, tool execution, and catalog APIs.
- Build the Python integrator pipeline for discovery, reader, codegen, test/fix, and publish.
- Build the Next.js dashboard for catalog, wallet, credentials, live feed, and integration requests.
- Keep shared JSON contracts aligned across the frontend and backend.
- Add smoke tests for the critical demo path.
- Debug service boundaries, API responses, and tool execution behavior.

This project was designed with Codex, built with Codex, and made useful for Codex.

## Why It Would Not Be Possible Without Codex

FuseKit depends on Codex in two ways.

First, Codex made the hackathon build possible. The product has a frontend, MCP server, backend APIs, wallet layer, database models, integration pipeline, contracts, and tests. Building that much reliable infrastructure in hackathon time would not be realistic without Codex acting as a fast engineering collaborator.

Second, the product itself only works because Codex can do real engineering work. When FuseKit sees a missing capability, the hard part is not saving a row in a database. The hard part is reading unfamiliar API docs, understanding auth and schemas, writing an adapter, testing it, fixing errors, and turning it into a reusable tool. That is exactly where Codex changes the shape of the problem.

Without Codex, FuseKit would be a normal static API marketplace. With Codex, it becomes a marketplace that can grow while the developer is still in the workflow.

## Demo Flow

1. Codex connects to FuseKit through one MCP URL.
2. Codex calls `tools/list` and sees the live catalog.
3. Codex executes tools like scraping, email, and SMS.
4. FuseKit checks wallet balance before each call.
5. If a requested tool is missing, FuseKit returns `TOOL_NOT_FOUND`.
6. That missing tool becomes an integration job.
7. Codex reads docs, generates code, tests/fixes the adapter, and publishes it.
8. The new tool appears in the catalog and becomes reusable through MCP and HTTP.

## Project Structure

```text
apps/web
  Next.js dashboard for the marketplace experience.

services/platform
  FastAPI MCP server, catalog APIs, wallet checks, tool execution, and logs.

services/integrator
  Codex-powered integration pipeline for missing API tools.

packages/contracts
  Shared JSON contracts used by frontend and backend services.

infra
  Database migrations, Docker resources, and local infrastructure files.

scripts
  Smoke tests, seed helpers, and contract validation.
```

## Core Contracts

FuseKit keeps these paths stable for the demo:

- MCP `tools/list`
- MCP `tools/call`
- `GET /api/catalog`
- `GET /api/catalog/recent`
- `GET /api/wallet/balance`
- `POST /api/wallet/topup`
- `POST /api/integrate`
- `POST /api/execute/{tool_name}`
- `GET /api/capabilities/{tool_name}/manifest`

## What Judges Should Notice

FuseKit is not trying to replace Codex with another planner. It gives Codex stronger hands.

Codex already knows how to reason about a developer's goal. FuseKit gives it a live tool layer: discover what exists, execute real APIs, charge safely, and create new tools when the catalog is missing something.

The result is a working platform loop:

```text
Need tool -> discover -> execute -> bill -> log -> missing? -> integrate -> publish -> reuse
```

That loop is the core of FuseKit.

## Built For The OpenAI Codex Hackathon

FuseKit shows what becomes possible when Codex is treated as an engineering collaborator, not just a code generator. It helped build the platform, and the platform gives Codex a reusable way to work with real-world APIs.

## License

MIT
