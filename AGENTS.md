# Agent.md

## Purpose

This repository is now organized for a split architecture:

- `apps/web`: Next.js marketplace frontend
- `services/platform`: Python MCP server + backend API
- `services/integrator`: Python integration pipeline
- `packages/contracts`: shared JSON contracts

Use this file as the implementation guide for humans and coding agents.

## System Boundary

Codex runs in OpenAI Cloud and calls your MCP server URL.
Your platform is responsible for:

- `tools/list`
- `tools/call`
- wallet checks and deductions
- tool registry and catalog APIs
- integration trigger when a tool is missing

Your platform is not responsible for building an in-house planner agent in v1.

## Folder Ownership

### `apps/web`

Owns user-facing demo surfaces:

- catalog browser
- live integration feed
- wallet panel
- docs URL integration trigger form

### `services/platform`

Owns MCP and backend APIs:

- tool registry reads
- tool execution routing
- wallet middleware
- credential loading
- execution and billing logs

### `services/integrator`

Owns auto-integration pipeline:

1. discovery
2. reader
3. codegen
4. test/fix
5. publish

### `packages/contracts`

Owns cross-service contracts consumed by both TypeScript and Python code.

## Required Contracts

The following interface contracts must stay consistent:

1. Tool definition model stored in DB and returned via `tools/list`.
2. Integration trigger API: `POST /integrate`.
3. Website API:
- `GET /api/catalog`
- `GET /api/catalog/recent`
- `GET /api/wallet/balance`
- `POST /api/wallet/topup`
- `POST /api/integrate`
4. MCP error codes:
- `TOOL_NOT_FOUND`
- `INSUFFICIENT_FUNDS`

## Demo Critical Path

The demo is considered successful only if this path works end-to-end:

1. Codex reaches MCP URL and receives valid `tools/list`.
2. Codex executes at least `scrape_url`, `send_email`, and `send_sms`.
3. Wallet checks run before each `tools/call`.
4. Missing tool path triggers integration pipeline.
5. New tool becomes visible in catalog.
6. Final result is delivered (email/SMS/data fetch).

## Build Principles

- Keep the frontend thin and visual.
- Keep business logic out of `apps/web`.
- Keep MCP error responses deterministic.
- Prefer simple polling over real-time push for v1.
- Favor deterministic integration with bounded retries over autonomous complexity.
- Do not auto-acquire third-party credentials.

## Working Rules

- Read and respect [`AGENTS.md`](/home/vansh5632/Development/fusekit/AGENTS.md) before touching Next.js code.
- Keep changes scoped to one subsystem when possible.
- Add or update contracts first when changing cross-service behavior.
- Write or update one smoke test whenever changing demo critical path behavior.

