# FuseKit — 4-Agent Parallel Build Plan

> Each agent owns a distinct directory. Zero file conflicts. All four run simultaneously.

```
Time ────────────────────────────────────────────────────────────►

Agent 1 (Platform):   ██████████████████████████████████  independent
Agent 2 (Integrator): ██████████████████████████████████  independent
Agent 3 (Frontend):   ██████████████████████████████████  independent
Agent 4 (Infra/E2E):  ████████ Phase A ████████──wait──▶ Phase B (needs 1+2)
```

---

## Current State (Before Any Agent Starts)

| Component | Status | Detail |
|-----------|--------|--------|
| `services/platform/` | ~85% done | MCP server, wallet, 5 tools, seed script all functional. Has duplicate code bug in `main.py`. Missing `/api/catalog/recent`, `/api/integrate` endpoints. |
| `services/integrator/` | ~5% done | Only `config.py` exists. Zero pipeline code. |
| `apps/web/` | ~20% done | Default Next.js template. Zero FuseKit UI. |
| `packages/contracts/` | 100% done | All 5 JSON schemas complete. |
| `scripts/` | 100% done | Seed script works. |
| `infra/` | ~60% done | Docker + Postgres works. No Alembic migrations. No integrator service. |
| Tests | 0% | No test files anywhere. |

---

## Agent 1 — Platform Backend Completion

**Owns:** `services/platform/`  
**Goal:** Fix bugs, add missing API endpoints, wire MCP → integration trigger, write tests.

### Step 1: Fix `main.py` duplicate code
**Do:** Remove lines 84–140 in `services/platform/app/main.py` — they are a verbatim copy of lines 1–83 (duplicate `lifespan`, `app`, routes, SSE transport, `main()`).  
**Achieve:** Platform server starts cleanly without conflicting route definitions. Single source of truth for the FastAPI app.

### Step 2: Add `requested_tool_name` to IntegrationJob model
**Do:** In `services/platform/app/models.py`, add a `requested_tool_name: Mapped[str]` column to the `IntegrationJob` class.  
**Achieve:** Integration jobs can track which specific tool was requested, enabling the pipeline to name the generated tool correctly.

### Step 3: Add `GET /api/catalog/recent` endpoint
**Do:** In `services/platform/app/api/catalog.py`, add a `/recent` route that returns tools created in the last 24 hours.  
**Achieve:** Frontend live feed has a data source. Contract from `AGENTS.md` is satisfied (`GET /api/catalog/recent`).

### Step 4: Create `POST /api/integrate` endpoint
**Do:** Create new file `services/platform/app/api/integrations.py` with:
- `POST /api/integrate` — accepts `{docs_url, requested_by, requested_tool_name}`, creates `IntegrationJob` row, forwards to integrator service via HTTP, returns `{job_id, status: "queued"}`.
- `GET /api/integrate/{job_id}` — returns job status (queued/running/complete/failed) with current stage info.
- Register the router in `main.py`.

**Achieve:** Frontend integration form has a backend. The integrator service has a trigger path. Contract from `AGENTS.md` is satisfied (`POST /api/integrate`).

### Step 5: Wire TOOL_NOT_FOUND to auto-enqueue integration
**Do:** In `services/platform/app/mcp_server.py`, inside the `call_tool()` handler, when a tool is not found:
1. Create an `IntegrationJob` row in the DB with `triggered_by="mcp"`.
2. Optionally forward to integrator service (non-blocking).
3. Keep the existing `TOOL_NOT_FOUND` error response.

**Achieve:** The core demo flow works: Codex requests a missing tool → platform automatically queues an integration job → pipeline picks it up → tool becomes available. This is the "self-growing catalog" behavior.

### Step 6: Set up Alembic migrations
**Do:** Initialize Alembic config in `infra/alembic/`, point it at the platform models, generate the initial migration from all current models (`User`, `ToolDefinition`, `WalletTransaction`, `ToolCallLog`, `IntegrationJob`).  
**Achieve:** Database schema is version-controlled. No more relying on `create_all()` in the seed script. Production-safe schema management.

### Step 7: Write pytest test suite
**Do:** Create test files in `services/platform/tests/`:
- `test_wallet_service.py` — unit tests for `check_and_deduct`, `refund`, `topup`, `InsufficientFundsError`.
- `test_catalog_api.py` — test `GET /api/catalog`, `GET /api/catalog/recent`, `GET /api/catalog/stats`.
- `test_wallet_api.py` — test `GET /api/wallet/balance`, `POST /api/wallet/topup`, `GET /api/wallet/transactions`.
- `test_integrations_api.py` — test `POST /api/integrate`, `GET /api/integrate/{job_id}`.
- `conftest.py` — async DB fixtures, test client setup.

**Achieve:** All platform logic is verified. Regressions are caught. Confidence that MCP + wallet + catalog + integration trigger all work correctly.

### After Agent 1 completes:
- ✅ Platform server starts without errors
- ✅ MCP `tools/list` returns 5 live tools
- ✅ MCP `tools/call` executes tools with wallet enforcement
- ✅ Missing tool requests auto-create integration jobs
- ✅ All 7 REST API endpoints respond correctly
- ✅ Database schema is migration-managed
- ✅ Full test coverage for platform logic

---

## Agent 2 — Integration Pipeline

**Owns:** `services/integrator/`  
**Goal:** Build the real OpenAI-powered autonomous integration pipeline — all 5 stages.

### Step 1: Create FastAPI app entry point
**Do:** Create `services/integrator/app/main.py` with:
- `POST /integrate` — accepts `{docs_url, requested_by, requested_tool_name}`, kicks off pipeline, returns `{job_id, status: "queued"}`.
- `GET /integrate/{job_id}` — returns job status with stage progress.
- Background task execution for the pipeline (so the HTTP response returns immediately).

**Achieve:** Integrator is a running service with a stable API. Platform can trigger it via HTTP. Job tracking is available.

### Step 2: Build Discovery agent
**Do:** Create `services/integrator/app/agents/discovery.py`:
- Input: a docs URL.
- Fetch the page content (httpx + BeautifulSoup).
- Send to OpenAI GPT-4o with a structured prompt asking for: provider name, base URL, auth method (API key / Bearer / OAuth / none), key endpoints (up to 5), rate limits, sandbox availability.
- Output: structured JSON (`DiscoveryResult`).

**Achieve:** Given any API docs URL, we can automatically identify what the API is, how it authenticates, and its main endpoints. This is the foundation for all subsequent stages.

### Step 3: Build Reader agent
**Do:** Create `services/integrator/app/agents/reader.py`:
- Input: docs URL + `DiscoveryResult`.
- Fetch full docs content (follow pagination / sub-pages if needed).
- Send to OpenAI with a prompt to extract: endpoint paths, HTTP methods, required/optional parameters with types, request body schemas, response schemas, error codes.
- Output: structured JSON (`APISpecification`) — a machine-readable API surface.

**Achieve:** We have a complete, structured representation of the API's capabilities. This is what the code generator needs to write a working wrapper.

### Step 4: Build Codegen agent
**Do:** Create `services/integrator/app/agents/codegen.py`:
- Input: `APISpecification` + `requested_tool_name`.
- Send to OpenAI with a prompt that includes:
  - The tool definition schema from `packages/contracts/tool-definition.schema.json`.
  - Example tool implementations (e.g., `scrape_url.py`, `send_email.py` from `services/platform/app/tools/`).
  - Instructions to generate: an async `execute(**kwargs)` function, proper httpx usage, error handling, credential loading from env vars.
- Output: `GeneratedTool` — contains the Python source code, tool name, description, input_schema, output_schema, provider, cost_per_call.

**Achieve:** Given an API specification, we can generate a working Python tool wrapper that matches our platform's format exactly. The generated code follows the same patterns as our hand-written tools.

### Step 5: Build Test/Fix agent
**Do:** Create `services/integrator/app/agents/test_fix.py`:
- Input: `GeneratedTool`.
- Write the generated code to a temp file, dynamically import it.
- Construct a test call with safe/minimal parameters.
- Execute the function, inspect the response.
- On failure: send the error traceback + original code to OpenAI, ask for a fix, apply the fix, retry.
- Retry up to `max_fix_attempts` (default 3) times.
- Output: `TestResult` — success/failure, final code (possibly patched), error log.

**Achieve:** Generated tools are validated against real APIs before being published. Self-correction means most fixable bugs are resolved without human intervention. Failed tools don't pollute the catalog.

### Step 6: Build Publisher
**Do:** Create `services/integrator/app/publishers/db_writer.py`:
- Input: `GeneratedTool` (validated) + `TestResult`.
- On success:
  - Write the Python file to `services/platform/app/tools/{tool_name}.py`.
  - Insert a `ToolDefinition` row in the platform DB with status `live`.
  - Update the `IntegrationJob` row: status `complete`, `resulting_tool_id`, `completed_at`.
- On failure:
  - Update the `IntegrationJob` row: status `failed`, `error_log`.

**Achieve:** Successfully tested tools are automatically registered in the catalog and become callable via MCP. The full pipeline is closed — from docs URL to live tool with zero human intervention.

### Step 7: Build Pipeline orchestrator
**Do:** Create `services/integrator/app/pipeline.py`:
- Chains: Discovery → Reader → Codegen → Test/Fix → Publish.
- Updates `IntegrationJob.current_stage` at each transition.
- Handles errors at each stage gracefully (log + mark failed).
- Emits structured logs for observability.

**Achieve:** All 5 stages run as a single coordinated pipeline. Stage transitions are tracked in the DB so the UI can show progress. Failures at any stage are caught and logged cleanly.

### Step 8: Write tests
**Do:** Create tests in `services/integrator/tests/`:
- `test_discovery.py` — mock OpenAI responses, verify `DiscoveryResult` structure.
- `test_reader.py` — mock OpenAI, verify `APISpecification` output.
- `test_codegen.py` — mock OpenAI, verify generated code is valid Python.
- `test_pipeline.py` — integration test for the full pipeline with mocked external calls.
- `conftest.py` — fixtures for OpenAI mocking, test DB.

**Achieve:** Pipeline stages are individually verified. Regressions caught early. Can test without burning OpenAI credits.

### After Agent 2 completes:
- ✅ Integrator service runs and accepts `POST /integrate`
- ✅ Given a docs URL, the pipeline discovers → reads → generates → tests → publishes a new tool
- ✅ Generated tools match the platform's `ToolDefinition` format exactly
- ✅ Failed integrations are logged without corrupting the catalog
- ✅ Self-correction fixes common code generation errors
- ✅ Full test coverage with mocked OpenAI

---

## Agent 3 — Frontend Marketplace

**Owns:** `apps/web/`  
**Goal:** Build the complete marketplace UI — catalog browser, wallet panel, live feed, integration trigger, connect instructions.

### Step 1: Create branded layout and navigation
**Do:** Replace `apps/web/app/layout.tsx` with a FuseKit-branded layout:
- Top nav or sidebar with links: **Catalog**, **Wallet**, **Live Feed**, **Integrate**, **Connect**.
- FuseKit logo/wordmark.
- Dark mode support via Tailwind.
- Responsive container.

**Achieve:** Every page shares a consistent navigation structure. Users can move between all marketplace surfaces. The app looks like a real product, not a Next.js template.

### Step 2: Create API client library
**Do:** Create `apps/web/lib/api.ts` with typed fetch wrappers:
- `getCatalog(filters?)` → `GET /api/catalog`
- `getRecentTools()` → `GET /api/catalog/recent`
- `getCatalogStats()` → `GET /api/catalog/stats`
- `getWalletBalance()` → `GET /api/wallet/balance`
- `topUpWallet(amount)` → `POST /api/wallet/topup`
- `getTransactions()` → `GET /api/wallet/transactions`
- `getUsage()` → `GET /api/wallet/usage`
- `triggerIntegration(docsUrl, toolName?)` → `POST /api/integrate`
- `getJobStatus(jobId)` → `GET /api/integrate/{job_id}`
- Base URL configurable via env var `NEXT_PUBLIC_API_URL`.

**Achieve:** All API calls are centralized, typed, and reusable. Every page component imports from one place. Changing the backend URL requires changing one env var.

### Step 3: Build landing page
**Do:** Replace `apps/web/app/page.tsx` with:
- Hero section: "The API execution layer for the agentic era" — explain what FuseKit does.
- Quick stats pulled from `/api/catalog/stats`: total tools, live tools, categories.
- CTA buttons: "Browse Catalog" and "Connect Codex".
- Recently added tools section (from `/api/catalog/recent`).

**Achieve:** Users landing on the site immediately understand what FuseKit is. Live data from the backend proves the system is real. Clear entry points to the two main flows (browse tools, connect agent).

### Step 4: Build Catalog browser page
**Do:** Create `apps/web/app/catalog/page.tsx` with:
- Grid or table of all tools from `GET /api/catalog`.
- Filter dropdowns: status (live / pending / deprecated), category (communication, data_retrieval, search, etc.).
- Each tool card shows: name, description, provider, cost per call, status badge (green for live, yellow for pending, red for deprecated), category tag.
- Auto-refresh via polling every 5 seconds (so new tools appear when pipeline publishes them).

**Achieve:** The "living catalog" is visible. Users can see every tool available to their Codex agent. When the integration pipeline publishes a new tool, it appears in the catalog within 5 seconds — this is a key demo moment.

### Step 5: Build Wallet panel page
**Do:** Create `apps/web/app/wallet/page.tsx` with:
- Current balance display (large number, prominent).
- Top-up form: amount input + "Add Credits" button → calls `POST /api/wallet/topup`.
- Transaction history table from `GET /api/wallet/transactions`: date, type (debit/credit), amount, tool name, balance after.
- Per-tool usage breakdown from `GET /api/wallet/usage`.
- Auto-refresh balance every 5 seconds.

**Achieve:** Users can see their credit balance, add funds, and understand exactly what they're spending on. Balance updates live as Codex makes tool calls — another key demo visual.

### Step 6: Build Live integration feed page
**Do:** Create `apps/web/app/feed/page.tsx` with:
- List of recent integration activity:
  - Recently added tools (from `/api/catalog/recent`) with "NEW" badges.
  - In-progress integration jobs (if endpoint available) with stage indicators (discovery → reader → codegen → test → publish).
- Auto-refresh every 5 seconds.
- Timeline-style layout: newest at top.

**Achieve:** The "self-growing catalog" is visible in real-time. When a missing tool triggers the pipeline, users see the integration progress live. This is the centerpiece demo surface.

### Step 7: Build Integration trigger form page
**Do:** Create `apps/web/app/integrate/page.tsx` with:
- Form fields: Docs URL (required), Tool name suggestion (optional).
- Submit button → calls `POST /api/integrate`.
- After submission: show job ID, poll `GET /api/integrate/{job_id}` every 3 seconds, display stage progress inline.
- Success state: "Tool published! View in catalog" with link.
- Failure state: error message from pipeline.

**Achieve:** Users (and demo operators) can manually trigger the integration pipeline. The full journey from "paste a URL" to "tool is live" is visible on one page.

### Step 8: Build Connect page
**Do:** Create `apps/web/app/connect/page.tsx` with:
- Step-by-step instructions for adding MCP URL to Codex.
- Copyable MCP endpoint URL (`http://your-domain:8000/mcp/sse`).
- Demo auth token display (for hackathon: `demo-token-fusekit-2026`).
- Example Codex configuration snippet.

**Achieve:** Anyone can connect their Codex instance to the platform in under a minute. Clear, copy-paste instructions eliminate setup friction.

### Step 9: Build shared components
**Do:** Create in `apps/web/components/`:
- `Nav.tsx` — navigation bar used by layout.
- `CatalogTable.tsx` — reusable tool table/grid.
- `ToolCard.tsx` — individual tool card with status badge.
- `StatusBadge.tsx` — colored badge for live/pending/deprecated/integrating.
- `WalletCard.tsx` — balance display widget.
- `LiveFeed.tsx` — feed item component.
- `DocsUrlForm.tsx` — integration trigger form.
- `StatsBar.tsx` — catalog stats display.

**Achieve:** UI components are reusable and consistent. Building new pages is fast. Visual language is uniform across the app.

### After Agent 3 completes:
- ✅ Landing page shows live catalog stats and recently added tools
- ✅ Catalog page displays all tools with filtering and auto-refresh
- ✅ Wallet page shows balance, allows top-up, displays transaction history
- ✅ Live feed shows integration pipeline progress in real-time
- ✅ Integration form lets users trigger pipeline from a docs URL
- ✅ Connect page has copy-paste instructions for Codex setup
- ✅ All pages are responsive, dark-mode ready, and poll for updates

---

## Agent 4 — Infra, E2E Testing, and Demo Wiring

**Owns:** `infra/`, `scripts/`, `.env.example`, `mprocs.yaml`, cross-service tests  
**Goal:** Wire all services together, set up infrastructure, write the end-to-end smoke test that proves the demo works.

### Phase A — Infrastructure (runs in parallel with Agents 1–3)

#### Step 1: Create `.env.example`
**Do:** Create `.env.example` at repo root documenting every environment variable:
```
# Database
DATABASE_URL=postgresql+asyncpg://fusekit:fusekit@localhost:5432/fusekit

# Platform
API_HOST=0.0.0.0
API_PORT=8000
INTEGRATOR_URL=http://localhost:8001

# OpenAI (required for integration pipeline)
OPENAI_API_KEY=sk-...

# Tool credentials
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=+1...
RESEND_API_KEY=re_...
SERPER_API_KEY=...
APIFY_TOKEN=apify_...
PH_TOKEN=...
```

**Achieve:** Any developer (or agent) can clone the repo and know exactly which secrets are needed. No more guessing env var names.

#### Step 2: Create Dockerfile for integrator
**Do:** Create `infra/Dockerfile.integrator`:
- Python 3.12 slim base.
- Install `services/integrator` dependencies from `pyproject.toml`.
- Copy integrator source.
- Expose port 8001.
- CMD: `uvicorn app.main:app --host 0.0.0.0 --port 8001`.

**Achieve:** Integrator service is containerized. Can run alongside platform + postgres in Docker Compose.

#### Step 3: Update docker-compose.yml
**Do:** Edit `infra/docker-compose.yml`:
- Add `integrator` service (builds from `Dockerfile.integrator`, depends on postgres, shares network).
- Add `INTEGRATOR_URL=http://integrator:8001` to platform service env.
- Ensure all three services (postgres, platform, integrator) start together.

**Achieve:** `docker compose up` starts the entire stack: database, platform, integrator. One command to run everything.

#### Step 4: Update mprocs.yaml for local dev
**Do:** Edit `mprocs.yaml`:
- Add integrator process: `cd services/integrator && uvicorn app.main:app --port 8001 --reload`.
- Verify postgres, platform, and frontend processes are correct.

**Achieve:** `mprocs` runs all 4 processes (postgres, platform, integrator, frontend) in one terminal with labeled output. Fast local development.

#### Step 5: Initialize Alembic
**Do:** In `infra/alembic/`:
- Create `alembic.ini` pointing at the platform models.
- Create `env.py` with async SQLAlchemy config.
- Generate initial migration from all models.

**Achieve:** Database schema is version-controlled and reproducible. `alembic upgrade head` sets up tables correctly on any fresh database.

---

### Phase B — E2E Testing (after Agents 1 + 2 have APIs ready)

#### Step 6: Write the demo smoke test
**Do:** Create `scripts/smoke_demo.py` — a single script that runs the exact demo critical path:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | `GET /health` | `{"status": "ok"}` |
| 2 | MCP `tools/list` via SSE | Returns 5 tools with correct schemas |
| 3 | MCP `tools/call` for `scrape_url` | Returns scraped content, no error |
| 4 | `GET /api/wallet/balance` | Balance decreased by `scrape_url` cost |
| 5 | MCP `tools/call` for non-existent tool | Returns `TOOL_NOT_FOUND` |
| 6 | `GET /api/integrate/{job_id}` | IntegrationJob was created (from step 5) |
| 7 | `POST /api/integrate` with known docs URL | Returns `{job_id, status: "queued"}` |
| 8 | Poll job status until complete | Status transitions: queued → running → complete |
| 9 | MCP `tools/list` | New tool appears in list |
| 10 | MCP `tools/call` for the new tool | Executes successfully |

Print pass/fail for each step. Exit non-zero on any failure.

**Achieve:** One command proves the entire demo works end-to-end. Run it before any demo, presentation, or PR merge. This is the single most valuable test in the repo.

#### Step 7: Write contract validation script
**Do:** Create `scripts/validate_contracts.py`:
- Fetch responses from all platform API endpoints.
- Validate each response against its corresponding JSON schema in `packages/contracts/`.
- Report mismatches.

**Achieve:** Platform API never drifts from the contract. Frontend and integrator can rely on the documented schemas. Cross-service consistency is enforced.

#### Step 8: Write integration tests
**Do:** Create `tests/e2e/`:
- `test_wallet_enforcement.py` — verify insufficient funds blocks tool calls, refund on failure.
- `test_integration_trigger.py` — verify TOOL_NOT_FOUND creates job, POST /integrate works.
- `test_concurrent_calls.py` — verify wallet deductions are atomic under concurrent MCP calls.

**Achieve:** Edge cases are covered. Wallet can't go negative. Concurrent agent sessions don't cause race conditions. Integration trigger path is reliable.

#### Step 9: Demo reliability hardening
**Do:**
- Add retry decorator to tool implementations for flaky external API calls.
- Add cache fallback for scrape_url and get_producthunt (return cached result if live call fails).
- Verify all error responses match `packages/contracts/tool-call-error.schema.json`.
- Create a `scripts/preflight.sh` that checks: postgres is running, seed data exists, all env vars are set, platform health is ok.

**Achieve:** Demo never fails due to transient API errors or missing config. Stage-proof reliability.

### After Agent 4 completes:
- ✅ `docker compose up` starts postgres + platform + integrator
- ✅ `mprocs` runs all services + frontend locally
- ✅ `.env.example` documents every required secret
- ✅ Alembic manages database schema
- ✅ `python scripts/smoke_demo.py` proves the full demo critical path
- ✅ Contract validation catches API drift
- ✅ Integration tests cover wallet enforcement and concurrent access
- ✅ Demo reliability measures handle flaky external APIs

---

## Post-Completion: What the Full System Looks Like

```
User adds MCP URL to Codex
         │
         ▼
Codex calls tools/list ──► Platform returns 5+ live tools
         │
         ▼
Codex calls tools/call ──► Platform: auth → wallet check → execute → return result
         │                                                    │
         │                              External APIs ◄───────┘
         │                              (Twilio, Resend, Apify, Serper)
         │
         ▼ (tool not found)
Platform returns TOOL_NOT_FOUND + creates IntegrationJob
         │
         ▼
Integrator pipeline runs: discover → read → codegen → test/fix → publish
         │
         ▼
New tool appears in catalog ──► Codex retries ──► Success
         │
         ▼
Frontend shows: catalog growing, wallet draining, integration progress
```

### The 5 things that prove the demo works:
1. **MCP tools/list** returns tools — Codex can see what's available
2. **MCP tools/call** executes scrape_url, send_email, send_sms — real API calls happen
3. **Wallet enforces payment** — balance drops, insufficient funds blocks calls
4. **Missing tool triggers pipeline** — the catalog grows itself
5. **Frontend shows it all** — catalog, wallet, live feed update in real-time
