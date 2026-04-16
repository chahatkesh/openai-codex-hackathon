from __future__ import annotations

import uuid

import pytest

from app.services.wallet_service import (
    InsufficientFundsError,
    check_and_deduct,
    refund,
    topup,
)
from tests.helpers import DummyResult, FakeSession


@pytest.mark.asyncio
async def test_check_and_deduct_success_creates_debit_transaction():
    session = FakeSession(execute_results=[DummyResult(100), DummyResult(None)])

    new_balance = await check_and_deduct(
        session,
        user_id=uuid.uuid4(),
        tool_name="scrape_url",
        cost=15,
    )

    assert new_balance == 85
    assert session.commits == 1
    assert len(session.added) == 1
    assert session.added[0].type == "debit"


@pytest.mark.asyncio
async def test_check_and_deduct_raises_when_balance_low():
    session = FakeSession(execute_results=[DummyResult(5)])

    with pytest.raises(InsufficientFundsError):
        await check_and_deduct(
            session,
            user_id=uuid.uuid4(),
            tool_name="scrape_url",
            cost=15,
        )


@pytest.mark.asyncio
async def test_refund_adds_credit_transaction():
    session = FakeSession(execute_results=[DummyResult(85), DummyResult(None)])

    new_balance = await refund(
        session,
        user_id=uuid.uuid4(),
        tool_name="scrape_url",
        cost=15,
    )

    assert new_balance == 100
    assert session.commits == 1
    assert session.added[0].type == "credit"


@pytest.mark.asyncio
async def test_topup_adds_credits():
    session = FakeSession(execute_results=[DummyResult(100), DummyResult(None)])

    new_balance = await topup(
        session,
        user_id=uuid.uuid4(),
        amount=50,
    )

    assert new_balance == 150
    assert session.commits == 1
    assert session.added[0].reference == "topup"
