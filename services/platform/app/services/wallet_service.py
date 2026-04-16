"""Wallet middleware — balance check + atomic deduction."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, WalletTransaction


class InsufficientFundsError(Exception):
    def __init__(self, balance: int, cost: int):
        self.balance = balance
        self.cost = cost
        super().__init__(f"Insufficient funds: balance={balance}, cost={cost}")


async def check_and_deduct(
    session: AsyncSession,
    user_id: uuid.UUID,
    tool_name: str,
    cost: int,
) -> int:
    """Check user balance and atomically deduct credits.

    Returns the new balance after deduction.
    Raises InsufficientFundsError if balance is too low.
    """
    # Fetch current balance with row-level lock
    result = await session.execute(
        select(User.wallet_balance).where(User.id == user_id).with_for_update()
    )
    balance = result.scalar_one()

    if balance < cost:
        raise InsufficientFundsError(balance, cost)

    new_balance = balance - cost

    # Deduct
    await session.execute(
        update(User).where(User.id == user_id).values(wallet_balance=new_balance)
    )

    # Record transaction
    txn = WalletTransaction(
        user_id=user_id,
        type="debit",
        amount=cost,
        tool_name=tool_name,
        reference=f"tool_call:{tool_name}",
        balance_after=new_balance,
    )
    session.add(txn)
    await session.commit()

    return new_balance


async def refund(
    session: AsyncSession,
    user_id: uuid.UUID,
    tool_name: str,
    cost: int,
) -> int:
    """Refund credits for a failed tool call."""
    result = await session.execute(
        select(User.wallet_balance).where(User.id == user_id).with_for_update()
    )
    balance = result.scalar_one()
    new_balance = balance + cost

    await session.execute(
        update(User).where(User.id == user_id).values(wallet_balance=new_balance)
    )

    txn = WalletTransaction(
        user_id=user_id,
        type="credit",
        amount=cost,
        tool_name=tool_name,
        reference=f"refund:{tool_name}",
        balance_after=new_balance,
    )
    session.add(txn)
    await session.commit()

    return new_balance


async def topup(
    session: AsyncSession,
    user_id: uuid.UUID,
    amount: int,
) -> int:
    """Add credits to user wallet."""
    result = await session.execute(
        select(User.wallet_balance).where(User.id == user_id).with_for_update()
    )
    balance = result.scalar_one()
    new_balance = balance + amount

    await session.execute(
        update(User).where(User.id == user_id).values(wallet_balance=new_balance)
    )

    txn = WalletTransaction(
        user_id=user_id,
        type="credit",
        amount=amount,
        reference="topup",
        balance_after=new_balance,
    )
    session.add(txn)
    await session.commit()

    return new_balance
