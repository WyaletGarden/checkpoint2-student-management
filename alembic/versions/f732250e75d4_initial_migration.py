"""initial migration

Revision ID: f732250e75d4
Revises: 
Create Date: 2026-10-13 16:37:19.482892

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f732250e75d4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "teachers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("teacher_code", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("degree", sa.String(), nullable=True),
    )
    op.create_index("ix_teachers_id", "teachers", ["id"])
    op.create_index("ix_teachers_teacher_code", "teachers", ["teacher_code"], unique=True)
    op.create_index("ix_teachers_email", "teachers", ["email"], unique=True)
    op.create_table(
        "classes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("class_code", sa.String(), nullable=False),
        sa.Column("class_name", sa.String(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teachers.id"), nullable=True),
    )
    op.create_index("ix_classes_id", "classes", ["id"])
    op.create_index("ix_classes_class_code", "classes", ["class_code"], unique=True)
    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("student_code", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("major", sa.String(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("classes.id"), nullable=False),
    )
    op.create_index("ix_students_id", "students", ["id"])
    op.create_index("ix_students_student_code", "students", ["student_code"], unique=True)
    op.create_index("ix_students_email", "students", ["email"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("students")
    op.drop_table("classes")
    op.drop_table("teachers")
