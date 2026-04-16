# Agent 1 Implementation Report (Platform Backend)

## Overview
This document summarizes the backend work completed for **Agent 1** in `services/platform`, including MCP behavior updates, missing API endpoints, migration setup, and test scaffolding.

## What Was Implemented

### 1. Platform boot/runtime stabilization
- Removed duplicated FastAPI app block and kept a single canonical app setup.
- Registered integrations router in the main app.
- Fixed broken wallet service import path.

Updated file:
- `services/platform/app/main.py`
- `services/platform/app/services/wallet_service.py`

### 2. Integration job model update
- Added `requested_tool_name` column to `IntegrationJob`.

Updated file:
- `services/platform/app/models.py`

### 3. Catalog API completion
- Added `GET /api/catalog/recent` endpoint.
- Returns tools created in last 24 hours.
- Supports `limit` with capping.

Updated file:
- `services/platform/app/api/catalog.py`

### 4. Integrations API (new)
- Added `POST /api/integrate`.
  - Accepts `docs_url`, `requested_by`, `requested_tool_name`.
  - Persists `IntegrationJob` with queued status.
  - Best-effort background forward to integrator.
- Added `GET /api/integrate/{job_id}`.
  - Returns job status/stage/error/timestamps.

New file:
- `services/platform/app/api/integrations.py`

### 5. Shared integration service helpers (new)
- Added helper module for:
  - deterministic tool-miss docs URL: `mcp://tool-miss/<tool_name>`
  - job creation
  - non-blocking forward to integrator
  - status serialization

New file:
- `services/platform/app/services/integrations_service.py`

### 6. MCP TOOL_NOT_FOUND auto-enqueue behavior
- Updated MCP `call_tool` flow so missing tools now:
  - create an `IntegrationJob` (`triggered_by="mcp_tool_miss"`)
  - set synthetic docs URL placeholder
  - attempt best-effort forward to integrator
  - still return deterministic `TOOL_NOT_FOUND` text response

Updated file:
- `services/platform/app/mcp_server.py`

### 7. Alembic migration scaffolding
- Added root Alembic config and env wiring to platform models.
- Ensured initial migration includes `requested_tool_name` in `integration_jobs`.

Added/updated files:
- `alembic.ini`
- `infra/alembic/env.py`
- `infra/alembic/script.py.mako`
- `infra/alembic/versions/20260413_0001_initial_platform_schema.py`

### 8. Seed script migration alignment
- Removed `create_all()` table creation from seed script.
- Seed now assumes schema is already migrated.

Updated file:
- `scripts/seed_demo_tools.py`

### 9. Test suite scaffolding
Added platform tests covering wallet, catalog, integrations, and MCP missing-tool queue behavior.

Added files:
- `services/platform/tests/helpers.py`
- `services/platform/tests/test_wallet_service.py`
- `services/platform/tests/test_catalog_api.py`
- `services/platform/tests/test_wallet_api.py`
- `services/platform/tests/test_integrations_api.py`
- `services/platform/tests/test_mcp_server.py`
- `services/platform/tests/__init__.py`
- `services/platform/tests/conftest.py`

## Prerequisites Required To Run These Changes Fully

## System prerequisites
- Python **3.11+** (recommended 3.11/3.12)
- PostgreSQL reachable by platform and Alembic
- `pip` (or your preferred Python package manager)

## Python dependencies (platform service)
Install dependencies from:
- `services/platform/pyproject.toml`

At minimum, runtime requires:
- `fastapi`
- `uvicorn[standard]`
- `sqlalchemy[asyncio]`
- `asyncpg`
- `alembic`
- `pydantic`
- `pydantic-settings`
- `mcp[cli]`
- `httpx`

For tests also install:
- `pytest`
- `pytest-asyncio`

## Environment variables
Required for these changes to behave fully:
- `DATABASE_URL` (async URL, e.g. `postgresql+asyncpg://...`)
- `DATABASE_URL_SYNC` (sync URL for Alembic, e.g. `postgresql://...`)
- `INTEGRATOR_URL` (maps to `integrator_url` setting; defaults to `http://localhost:8001`)

Optional provider credentials (for real tool execution):
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`
- `RESEND_API_KEY`
- `SERPER_API_KEY`
- `APIFY_API_TOKEN`
- `PRODUCTHUNT_API_TOKEN`

## Database and migration prerequisites
1. Ensure PostgreSQL is running.
2. Run migration:
   - `alembic upgrade head`
3. Seed demo data:
   - `python -m scripts.seed_demo_tools` (from `services/platform` context or with correct `PYTHONPATH`)

## How to run platform
From `services/platform`:
- `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

Health check:
- `GET /health`

## How to run tests
From `services/platform`:
- `pytest -q`

Note: In this environment, test execution failed initially due to missing `fastapi` installation. Ensure dependencies are installed before running tests.

## API additions included
- `GET /api/catalog/recent`
- `POST /api/integrate`
- `GET /api/integrate/{job_id}`

## Behavior changes included
- `TOOL_NOT_FOUND` now auto-creates an integration job and uses a synthetic placeholder docs URL.
