"""Initial platform schema

Revision ID: 20260413_0001
Revises:
Create Date: 2026-04-13 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260413_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("mcp_auth_token", sa.String(length=255), nullable=False),
        sa.Column("wallet_balance", sa.Integer(), nullable=False, server_default="10000"),
        sa.Column(
            "spending_limit_per_session",
            sa.Integer(),
            nullable=False,
            server_default="5000",
        ),
        sa.Column("low_balance_threshold", sa.Integer(), nullable=False, server_default="500"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("mcp_auth_token"),
    )

    op.create_table(
        "tool_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("cost_per_call", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="live"),
        sa.Column("input_schema", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "output_schema",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="other"),
        sa.Column("source", sa.String(length=20), nullable=False, server_default="seed"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("implementation_module", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(
        "ix_tool_definitions_name", "tool_definitions", ["name"], unique=False
    )

    op.create_table(
        "wallet_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("reference", sa.String(length=255), nullable=True),
        sa.Column("tool_name", sa.String(length=100), nullable=True),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_wallet_transactions_user_id",
        "wallet_transactions",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "tool_call_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column("input_args", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("result_status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("credits_deducted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("execution_duration_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tool_call_logs_user_id", "tool_call_logs", ["user_id"], unique=False)

    op.create_table(
        "integration_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("docs_url", sa.Text(), nullable=False),
        sa.Column("requested_tool_name", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="queued"),
        sa.Column("current_stage", sa.String(length=30), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_log", sa.Text(), nullable=True),
        sa.Column("resulting_tool_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("triggered_by", sa.String(length=30), nullable=False, server_default="user"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("integration_jobs")

    op.drop_index("ix_tool_call_logs_user_id", table_name="tool_call_logs")
    op.drop_table("tool_call_logs")

    op.drop_index("ix_wallet_transactions_user_id", table_name="wallet_transactions")
    op.drop_table("wallet_transactions")

    op.drop_index("ix_tool_definitions_name", table_name="tool_definitions")
    op.drop_table("tool_definitions")

    op.drop_table("users")
