#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
DATABASE_URL_SYNC="${DATABASE_URL_SYNC:-postgresql://fusekit:fusekit@localhost:5432/fusekit}"
SMOKE_MODE="${SMOKE_MODE:-stub}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[FAIL] Missing required command: $1"
    exit 1
  fi
}

check_env() {
  local var_name="$1"
  if [[ -z "${!var_name:-}" ]]; then
    echo "[FAIL] Required env var is missing: $var_name"
    exit 1
  fi
}

echo "[INFO] Running FuseKit preflight checks..."

require_cmd curl
require_cmd python
require_cmd psql

check_env DATABASE_URL
check_env DATABASE_URL_SYNC

if [[ "$SMOKE_MODE" == "live" ]]; then
  check_env OPENAI_API_KEY
fi

echo "[INFO] Checking postgres connectivity..."
psql "$DATABASE_URL_SYNC" -c 'select 1;' >/dev/null
echo "[PASS] Postgres is reachable"

echo "[INFO] Checking platform health..."
health_json="$(curl -fsS "$API_BASE_URL/health")"
echo "$health_json" | grep -q '"status"' || { echo "[FAIL] /health response missing status"; exit 1; }
echo "[PASS] Platform health endpoint reachable"

echo "[INFO] Checking seeded demo user/tools..."
python - <<'PY'
import asyncio
import os

import asyncpg

db_url = os.environ["DATABASE_URL"].replace("+asyncpg", "")

async def main() -> None:
    conn = await asyncpg.connect(db_url)
    try:
        user_count = await conn.fetchval("select count(*) from users where mcp_auth_token = 'demo-token-fusekit-2026'")
        tool_count = await conn.fetchval("select count(*) from tool_definitions where status = 'live'")
    finally:
        await conn.close()

    if user_count < 1:
        raise SystemExit("[FAIL] Demo user missing. Run seed script.")
    if tool_count < 5:
        raise SystemExit(f"[FAIL] Expected at least 5 live tools, found {tool_count}.")

    print("[PASS] Seeded demo data present")

asyncio.run(main())
PY

echo "[PASS] Preflight checks completed successfully."
