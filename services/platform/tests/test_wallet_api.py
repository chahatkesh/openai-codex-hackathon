from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.api.wallet import TopUpRequest, get_balance, get_transactions, get_usage, topup_wallet
from app.models import ToolCallLog, User, WalletTransaction
from tests.helpers import DummyResult, FakeSession



def _user() -> User:
    return User(
        id=uuid.uuid4(),
        email="demo@fusekit.dev",
        name="Demo",
        mcp_auth_token="demo-token-fusekit-2026",
        wallet_balance=100,
        spending_limit_per_session=5000,
        low_balance_threshold=500,
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_get_balance_returns_wallet_shape():
    session = FakeSession(execute_results=[DummyResult(_user())])

    payload = await get_balance(session=session)

    assert payload["balance"] == 100
    assert "spending_limit_per_session" in payload


@pytest.mark.asyncio
async def test_topup_wallet_calls_service(monkeypatch):
    session = FakeSession(execute_results=[DummyResult(_user())])

    async def fake_topup(_session, _user_id, _amount):
        return 150

    monkeypatch.setattr("app.api.wallet.wallet_topup", fake_topup)

    payload = await topup_wallet(req=TopUpRequest(amount=50), session=session)

    assert payload == {"balance": 150}


@pytest.mark.asyncio
async def test_get_transactions_returns_rows():
    now = datetime.now(timezone.utc)
    txn = WalletTransaction(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        type="debit",
        amount=10,
        reference="tool_call:scrape_url",
        tool_name="scrape_url",
        balance_after=90,
        created_at=now,
    )
    session = FakeSession(execute_results=[DummyResult(_user()), DummyResult([txn])])

    payload = await get_transactions(session=session)

    assert len(payload) == 1
    assert payload[0]["tool_name"] == "scrape_url"


@pytest.mark.asyncio
async def test_get_usage_aggregates_by_tool():
    now = datetime.now(timezone.utc)
    logs = [
        ToolCallLog(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            tool_name="scrape_url",
            input_args={},
            result_status="success",
            error_message=None,
            credits_deducted=15,
            execution_duration_ms=10,
            created_at=now,
        ),
        ToolCallLog(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            tool_name="scrape_url",
            input_args={},
            result_status="error",
            error_message="boom",
            credits_deducted=0,
            execution_duration_ms=12,
            created_at=now,
        ),
    ]
    session = FakeSession(execute_results=[DummyResult(_user()), DummyResult(logs)])

    payload = await get_usage(session=session)

    assert payload["total_calls"] == 2
    assert payload["by_tool"]["scrape_url"]["errors"] == 1
