"""Wallet API routes — /api/wallet."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import User, WalletTransaction, ToolCallLog
from app.services.wallet_service import topup as wallet_topup
from app.mcp_server import DEMO_USER_TOKEN

router = APIRouter(prefix="/api/wallet", tags=["wallet"])


async def _get_demo_user(session: AsyncSession) -> User:
    result = await session.execute(
        select(User).where(User.mcp_auth_token == DEMO_USER_TOKEN)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=500, detail="Demo user not found. Run the seed script.")
    return user


@router.get("/balance")
async def get_balance(session: AsyncSession = Depends(get_session)):
    """Get current wallet balance."""
    user = await _get_demo_user(session)
    return {
        "balance": user.wallet_balance,
        "spending_limit_per_session": user.spending_limit_per_session,
        "low_balance_threshold": user.low_balance_threshold,
    }


class TopUpRequest(BaseModel):
    amount: int


@router.post("/topup")
async def topup_wallet(req: TopUpRequest, session: AsyncSession = Depends(get_session)):
    """Add credits to wallet."""
    user = await _get_demo_user(session)
    if req.amount <= 0:
        return {"error": "Amount must be positive"}
    new_balance = await wallet_topup(session, user.id, req.amount)
    return {"balance": new_balance}


@router.get("/transactions")
async def get_transactions(
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
):
    """Get wallet transaction history."""
    user = await _get_demo_user(session)
    result = await session.execute(
        select(WalletTransaction)
        .where(WalletTransaction.user_id == user.id)
        .order_by(WalletTransaction.created_at.desc())
        .limit(min(limit, 200))
    )
    txns = result.scalars().all()

    return [
        {
            "id": str(t.id),
            "type": t.type,
            "amount": t.amount,
            "tool_name": t.tool_name,
            "reference": t.reference,
            "balance_after": t.balance_after,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in txns
    ]


@router.get("/usage")
async def get_usage(session: AsyncSession = Depends(get_session)):
    """Get tool usage summary."""
    user = await _get_demo_user(session)
    result = await session.execute(
        select(ToolCallLog)
        .where(ToolCallLog.user_id == user.id)
        .order_by(ToolCallLog.created_at.desc())
        .limit(100)
    )
    logs = result.scalars().all()

    # Aggregate by tool
    usage: dict[str, dict] = {}
    for log in logs:
        if log.tool_name not in usage:
            usage[log.tool_name] = {"calls": 0, "total_credits": 0, "errors": 0}
        usage[log.tool_name]["calls"] += 1
        usage[log.tool_name]["total_credits"] += log.credits_deducted
        if log.result_status == "error":
            usage[log.tool_name]["errors"] += 1

    return {
        "total_calls": len(logs),
        "by_tool": usage,
    }
