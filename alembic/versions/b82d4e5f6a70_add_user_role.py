"""Add constrained user roles, defaulting existing accounts to user.

Revision ID: b82d4e5f6a70
Revises: a91c2d3e4f50
"""
from alembic import op
import sqlalchemy as sa

revision = "b82d4e5f6a70"
down_revision = "a91c2d3e4f50"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("role", sa.String(5), nullable=False,
                                      server_default="user"))
        batch_op.create_check_constraint("ck_users_role", "role IN ('admin', 'user')")


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("ck_users_role", type_="check")
        batch_op.drop_column("role")
