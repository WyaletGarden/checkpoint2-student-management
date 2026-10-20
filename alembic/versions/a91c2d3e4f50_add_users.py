"""Add users for password authentication.

Revision ID: a91c2d3e4f50
Revises: f732250e75d4
"""
from alembic import op
import sqlalchemy as sa

revision = "a91c2d3e4f50"
down_revision = "f732250e75d4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(60), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("users")
