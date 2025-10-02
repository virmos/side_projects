"""create orders tables

Revision ID: 0001_create_orders
Revises: 
Create Date: 2025-08-10

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_create_orders"
down_revision = ""
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "order_header",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.String(255), nullable=False, index=True),
        sa.Column("order_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, index=True),
    )
    op.create_table(
        "order_line",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("order_header.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("product_id", sa.Integer(), nullable=False, index=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("order_line")
    op.drop_table("order_header")


