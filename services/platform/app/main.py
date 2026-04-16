"""FuseKit platform server — FastAPI app with MCP SSE + Streamable HTTP transports."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.responses import Response

from app.api.catalog import router as catalog_router
from app.api.integrations import router as integrations_router
from app.api.wallet import router as wallet_router
from app.config import settings
from app.mcp_server import mcp

# SSE transport (legacy clients)
sse = SseServerTransport("/messages/")

# Streamable HTTP session manager — handles session state across multiple requests
http_session_manager = StreamableHTTPSessionManager(app=mcp, stateless=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle — runs the HTTP session manager task group."""
    print("FuseKit platform service starting...")
    async with http_session_manager.run():
        yield
    print("FuseKit platform service shutting down.")


app = FastAPI(
    title="FuseKit Platform",
    description="MCP server + REST API for FuseKit",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API routes
app.include_router(catalog_router)
app.include_router(wallet_router)
app.include_router(integrations_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "fusekit-platform"}


# Raw ASGI sub-app for MCP — handles all MCP transports under /mcp/*
async def mcp_asgi_app(scope, receive, send):
    """Route MCP requests:
      GET  /sse        — SSE transport (legacy)
      POST /messages/  — SSE message posting
      ANY  /http       — Streamable HTTP (Codex 0.120+)
    """
    if scope["type"] == "lifespan":
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return
        return

    # Starlette passes the full path; root_path is the mount prefix (/mcp).
    # Strip mount prefix to get the sub-path.
    path = scope.get("path", "")
    root = scope.get("root_path", "")
    if root and path.startswith(root):
        path = path[len(root):] or "/"

    method = scope.get("method", "GET")

    if path == "/sse" and method == "GET":
        async with sse.connect_sse(scope, receive, send) as streams:
            await mcp.run(
                streams[0],
                streams[1],
                mcp.create_initialization_options(),
            )
    elif path.startswith("/messages") and method == "POST":
        await sse.handle_post_message(scope, receive, send)
    elif path in ("/http", "/http/"):
        # Streamable HTTP — session manager handles both POST and GET (SSE stream)
        await http_session_manager.handle_request(scope, receive, send)
    else:
        await Response("Not Found", status_code=404)(scope, receive, send)


app.mount("/mcp", mcp_asgi_app)
