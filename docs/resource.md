Here's a comprehensive breakdown of every resource you need and the best practices to follow — organized by role in your architecture.

---

## Docs & Resources by Layer

### 🐍 Python Basics (since you're new to it)

Before touching FastAPI or MCP, get comfortable with the essentials:

- **Official Python Tutorial** → [docs.python.org/3/tutorial](https://docs.python.org/3/tutorial/) — covers syntax, functions, classes, and type hints
- **Real Python** → [realpython.com](https://realpython.com) — extremely beginner-friendly articles on async/await, decorators, virtual environments
- **Python Type Hints** → [mypy.readthedocs.io](https://mypy.readthedocs.io/en/stable/getting_started.html) — FuseKit's entire Python stack relies on type hints; learn this early

The most important Python concepts for this project specifically are: `async/await`, `type hints`, `decorators` (`@app.get`), and `Pydantic models` (Python classes with typed fields).

---

### 1. FastAPI (Platform Backend + REST API)

FastAPI stands on the shoulders of Starlette for the web parts and Pydantic for the data parts. It gives you automatic interactive documentation at `/docs` — you can test every endpoint live without writing a separate test client.

- **Primary doc** → [fastapi.tiangolo.com](https://fastapi.tiangolo.com) — work through the full Tutorial–User Guide, not just the intro
- **Full-stack template** → [github.com/fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) — official reference app with FastAPI + React + SQLModel + Postgres + Docker, very close to your target architecture
- **TestDriven.io deep dive** → [testdriven.io/blog/fastapi-sqlmodel](https://testdriven.io/blog/fastapi-sqlmodel/) — covers async FastAPI + SQLModel + Alembic end-to-end

Sections to prioritize from the FastAPI docs: Path Parameters, Request Bodies, Dependency Injection, Background Tasks, and Security.

---

### 2. MCP Python SDK (MCP Server)

The MCP Python SDK implements the full MCP specification. It supports standard transports including stdio, SSE, and Streamable HTTP, and handles all MCP protocol messages and lifecycle events.

- **Official SDK repo** → [github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)
- **API reference** → [py.sdk.modelcontextprotocol.io](https://py.sdk.modelcontextprotocol.io)
- **MCP spec docs** → [modelcontextprotocol.io/docs/sdk](https://modelcontextprotocol.io/docs/sdk)

The key thing for FuseKit: the `FastMCP` class is a high-level interface for building MCP servers with minimal boilerplate. You can use `@mcp.tool()` decorator to register tools, and run it with `mcp.run(transport="streamable-http")` — which is what Codex will connect to.

For the `TOOL_NOT_FOUND` pattern your doc describes, study the low-level `Server` class examples in the SDK repo, since you need custom error handling that `FastMCP` abstracts away.

---

### 3. SQLModel + Alembic (Database Layer)

SQLModel combines Pydantic for data validation with SQLAlchemy as the ORM, so you write your data models once and get both the ORM representation and the Pydantic model for validation and serialization.

- **SQLModel docs** → [sqlmodel.tiangolo.com](https://sqlmodel.tiangolo.com)
- **Alembic official tutorial** → [alembic.sqlalchemy.org/en/latest/tutorial.html](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- **SQLModel + Alembic together** → [arunanshub.hashnode.dev/using-sqlmodel-with-alembic](https://arunanshub.hashnode.dev/using-sqlmodel-with-alembic) — the step-by-step you'll actually need
- **Full async example repo** → [github.com/testdrivenio/fastapi-sqlmodel-alembic](https://github.com/testdrivenio/fastapi-sqlmodel-alembic)

Alembic tracks changes in your models, creates migration scripts that apply schema changes safely, and lets you upgrade or downgrade your database schema version by version — think of it as a time machine for your database schema.

---

### 4. Stripe (Wallet / Payments)

- **Python quickstart** → [docs.stripe.com/get-started/development-environment?lang=python](https://docs.stripe.com/get-started/development-environment?lang=python)
- **Python SDK repo** → [github.com/stripe/stripe-python](https://github.com/stripe/stripe-python)
- **Full API reference** → [docs.stripe.com/api](https://docs.stripe.com/api)
- **Webhooks guide** → [docs.stripe.com/webhooks](https://docs.stripe.com/webhooks)

For FuseKit's wallet top-up, you only need two Stripe flows: **Payment Intents** (one-time top-up) and **Webhooks** (to confirm the payment landed and credit the wallet in your DB).

---

### 5. httpx (HTTP Client for Tool Calls)

- **Docs** → [www.python-httpx.org](https://www.python-httpx.org)

Use `httpx.AsyncClient` inside your tool implementations so the FastAPI async event loop is never blocked during third-party API calls.

---

### 6. Pydantic (Validation Everywhere)

- **Docs** → [docs.pydantic.dev](https://docs.pydantic.dev)

Every request/response body, tool definition, and contract schema in FuseKit should be a Pydantic model. This is the glue between FastAPI, SQLModel, and your JSON contracts.

---

### 7. pytest (Testing)

- **Docs** → [docs.pytest.org](https://docs.pytest.org)
- **FastAPI testing guide** → [fastapi.tiangolo.com/tutorial/testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

## Best Practices to Get the Best Output

### Python-specific (for beginners)

- **Always use virtual environments.** Use `uv` (the modern tool) or `python -m venv`. Never install packages globally.
- **Use type hints everywhere.** `def get_tool(tool_id: int) -> Tool:` — this is what powers both FastAPI's auto-docs and Pydantic validation.
- **Use `async def` for all FastAPI route handlers** and anything that does I/O (DB queries, HTTP calls). Use `def` only for pure computation.
- **Never hardcode secrets.** Use `.env` files + `python-dotenv` or `pydantic-settings` for config. Your doc already has a `.env.example` requirement — honor it from day one.

### FastAPI architecture

- **Use the Dependency Injection system** for DB sessions, credentials, and wallet auth. Don't pass a DB session manually into functions — let FastAPI inject it.
- **Put your routes in separate files** (`api/catalog.py`, `api/wallet.py`) and register them with `app.include_router()` in `main.py`. Your doc's structure already reflects this correctly.
- **Use Pydantic models for both input and output** — define a `ToolCreate` model for incoming data and a `ToolRead` model for what you return. Never return raw DB objects.

### MCP Server

- **Lock your contract JSON shapes first** before writing any code. Your doc already specifies `TOOL_NOT_FOUND` and `INSUFFICIENT_FUNDS` error codes — put these in `packages/contracts` and import them from there.
- **Start with `FastMCP`** for the 5 seeded tools, then drop to the low-level `Server` class only if you need custom error responses for the missing-tool trigger.
- **Mount MCP alongside FastAPI** using Starlette's `Mount` — the SDK supports this so you don't need two separate processes for the MCP server and REST API.

### Database

- **Always run `alembic revision --autogenerate` after changing a model** — never edit the DB schema by hand.
- **Use SQLite for the demo** as your doc recommends, with the `render_as_batch=True` Alembic option to handle SQLite's limited `ALTER TABLE` support.
- **Seed your 5 tools at startup** using `db/seed.py` — check if tools already exist before inserting so re-runs don't break.

### Demo reliability

- **Write `smoke_demo.sh` before building anything else.** Define the pass/fail criteria for each stage first — then build backwards to make those checks pass. This is the single highest-ROI practice for a hackathon.
- **Use polling (as specified)** — 5-second polling is fine and avoids the complexity of WebSocket/SSE for the demo. Don't over-engineer this.
- **Commit your `.env.example` with every key documented.** When Person 4 runs the smoke test on a fresh machine, missing env vars should be obvious immediately.

### General

- **Pin all dependency versions** in `pyproject.toml` — `fastapi==0.135.1`, not `fastapi>=0.100`. Hackathon environments need to be reproducible.
- **Use `docker-compose.yml`** from the `infra/` directory to spin up all three services (web, platform, integrator) in one command. Write this early so the whole team can develop consistently.