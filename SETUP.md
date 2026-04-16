# FuseKit Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- pnpm (`npm install -g pnpm`)

## First-Time Setup

### 1. Clone & Initialize
```bash
cd /Users/rishi/git/fusekit
pnpm setup  # Creates .venv, installs Python & Node deps
```

This command:
- Creates a Python virtual environment at `.venv/`
- Installs Python dependencies for `services/platform` and `services/integrator`
- Installs pnpm dependencies for `apps/web`

### 2. Start the Full Stack

```bash
pnpm dev
# or directly: mprocs
```

This will start in parallel:
- **PostgreSQL** (port 5432) via Docker
- **Platform MCP Server** (port 8000) — Reads tools from DB, handles tool execution
- **Integrator Service** (port 8001) — Auto-generates new tools from APIs
- **Next.js Frontend** (port 3000) — Marketplace UI

You'll see a split-pane terminal with each service. Use `x` to kill one, `q` to quit all.

### 3. Seed Demo Data

Once all services are healthy (green checkmarks in mprocs), run in another terminal:

```bash
pnpm db:seed
```

This creates:
- Demo user (token: `demo-token-fusekit-2026`)
- 5 built-in tools: `scrape_url`, `send_email`, `send_sms`, `search_web`, `get_producthunt`

### 4. Verify Everything Works

```bash
# Should return 5 tools
curl http://localhost:8000/api/catalog | jq '.tools | length'

# Check platform health
curl http://localhost:8000/api/catalog | jq .
```

If you see tool names, you're ready! 🎉

---

## Common Commands

```bash
pnpm dev              # Start full stack (postgres + platform + integrator + frontend)
pnpm web:dev         # Frontend only (for rapid iteration)
pnpm db:seed         # Seed demo user + 5 tools
pnpm db:migrate      # Run Alembic migrations
pnpm db:migration:create "add_users_table"  # Create a new migration
```

---

## Troubleshooting

### Port Already in Use (5432)

You may have leftover containers from other projects:

```bash
docker ps  # See all containers
docker stop <container_id>  # Stop the one using 5432
```

Then try `pnpm dev` again.

### Virtual Environment Not Activated

If you get `uvicorn: command not found`, mprocs will automatically activate the venv via:
```bash
source .venv/bin/activate
```

If that doesn't work, manually activate before running:
```bash
source .venv/bin/activate
pnpm dev
```

### PostgreSQL Connection Refused

Make sure the `infra/docker-compose.yml` postgres container is running:

```bash
docker compose -f infra/docker-compose.yml up postgres
```

In a separate terminal, then run `pnpm dev`.

### SWC Binary Error (Next.js)

On Apple Silicon Macs, Next.js sometimes needs to build SWC. Try:

```bash
cd apps/web
rm -rf .next node_modules
pnpm install
pnpm dev
```

---

## Architecture Quick Reference

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Shared database for tools, users, logs |
| Platform | 8000 | MCP server, tool registry, wallet, REST APIs |
| Integrator | 8001 | Auto-generation pipeline (discovery → codegen → test/fix) |
| Frontend | 3000 | Marketplace UI (catalog, wallet, live feed) |

All services connect to the same PostgreSQL instance. Both `platform` and `integrator` read/write tool definitions.

---

## Next Steps

- [ ] Run `pnpm dev` and verify all 4 services start
- [ ] Run `pnpm db:seed` to populate demo data
- [ ] Visit `http://localhost:3000` to see the marketplace
- [ ] Test tool calls via platform API or Codex integration
- [ ] Explore `services/integrator` to understand the auto-generation pipeline
