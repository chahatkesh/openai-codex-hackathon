# FuseKit Contracts — Tool Definition Schema

## Tool Definition (JSON Schema)

Every module (MCP server, catalog API, integration pipeline, seed scripts) reads and writes tools using this single format:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ToolDefinition",
  "type": "object",
  "required": ["name", "description", "provider", "cost_per_call", "status", "input_schema", "output_schema"],
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "name": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9_]*$",
      "description": "Snake_case identifier. Must be unique across the catalog."
    },
    "description": {
      "type": "string",
      "description": "Plain-English description shown to Codex so it knows when to call this tool."
    },
    "provider": {
      "type": "string",
      "description": "External API provider name, e.g. 'twilio', 'nylas', 'apify'."
    },
    "cost_per_call": {
      "type": "integer",
      "minimum": 1,
      "description": "Cost in platform credits per invocation."
    },
    "status": {
      "type": "string",
      "enum": ["live", "pending_credentials", "deprecated"]
    },
    "input_schema": {
      "type": "object",
      "description": "JSON Schema describing the tool's input parameters."
    },
    "output_schema": {
      "type": "object",
      "description": "JSON Schema describing the tool's output."
    },
    "category": {
      "type": "string",
      "enum": ["communication", "data_retrieval", "search", "payments", "productivity", "other"]
    },
    "source": {
      "type": "string",
      "enum": ["manual", "pipeline", "seed"],
      "default": "manual"
    },
    "version": { "type": "integer", "minimum": 1, "default": 1 },
    "implementation_module": {
      "type": "string",
      "description": "Python dotted path to the function, e.g. 'tools.scrape_url.execute'"
    },
    "created_at": { "type": "string", "format": "date-time" },
    "updated_at": { "type": "string", "format": "date-time" }
  }
}
```

## MCP Protocol Messages

### tools/list response item
```json
{
  "name": "scrape_url",
  "description": "Scrape a webpage and return its text content",
  "inputSchema": {
    "type": "object",
    "required": ["url"],
    "properties": {
      "url": { "type": "string", "description": "URL to scrape" }
    }
  }
}
```

### tools/call request
```json
{
  "name": "scrape_url",
  "arguments": {
    "url": "https://www.producthunt.com"
  }
}
```

### tools/call response (success)
```json
{
  "content": [
    { "type": "text", "text": "..." }
  ]
}
```

### tools/call response (error — insufficient funds)
```json
{
  "content": [
    { "type": "text", "text": "INSUFFICIENT_FUNDS: Your wallet balance is 0 credits. This tool costs 10 credits. Please top up at https://fusekit.dev/wallet" }
  ],
  "isError": true
}
```

### tools/call response (error — tool not found)
```json
{
  "content": [
    { "type": "text", "text": "TOOL_NOT_FOUND: 'send_slack_message' is not in the catalog. An integration job has been queued. Retry in a few minutes." }
  ],
  "isError": true
}
```

## Directory Layout

```
fusekit/
├── app/                    # Next.js marketplace frontend
│   ├── layout.tsx
│   ├── page.tsx            # Landing/catalog page
│   ├── globals.css
│   ├── catalog/
│   │   └── page.tsx        # Full catalog browse
│   ├── wallet/
│   │   └── page.tsx        # Wallet & transactions
│   └── connect/
│       └── page.tsx        # Connect Codex instructions
├── backend/                # Python backend
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   ├── server/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI app + MCP server entry
│   │   ├── config.py       # Settings from env
│   │   ├── db.py           # SQLAlchemy engine/session
│   │   ├── models.py       # ORM models
│   │   ├── mcp_server.py   # MCP protocol handler
│   │   ├── wallet.py       # Wallet middleware
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── catalog.py  # /api/catalog routes
│   │       └── wallet.py   # /api/wallet routes
│   └── tools/              # Tool implementations
│       ├── __init__.py
│       ├── registry.py     # Tool loader/registry
│       ├── scrape_url.py
│       ├── send_email.py
│       ├── send_sms.py
│       ├── search_web.py
│       └── get_producthunt.py
├── docker-compose.yml
├── Dockerfile.backend
├── mprocs.yaml
├── contracts.md            # This file
├── idea.md
├── plan.md
└── package.json
```
