"""add priority inputs to tasks

Revision ID: b83f0a92d4e1
Revises: 7ac36f9d1b24
Create Date: 2026-08-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b83f0a92d4e1"
down_revision: Union[str, Sequence[str], None] = "7ac36f9d1b24"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add deterministic priority inputs to tasks."""
    with op.batch_alter_table("tasks", recreate="always") as batch_op:
        batch_op.add_column(
            sa.Column(
                "task_type",
                sa.String(length=32),
                server_default=sa.text("'general'"),
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "effort_level",
                sa.Integer(),
                server_default=sa.text("1"),
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "recovery_buffer_minutes",
                sa.Integer(),
                server_default=sa.text("15"),
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "splittable",
                sa.Boolean(),
                server_default=sa.text("1"),
                nullable=False,
            )
        )
        batch_op.create_check_constraint(
            "ck_tasks_task_type_values",
            "task_type IN ('general', 'assignment', 'exam_preparation', "
            "'project', 'study', 'admin', 'chore', 'personal')",
        )
        batch_op.create_check_constraint(
            "ck_tasks_effort_level_range",
            "effort_level IN (0, 1, 2)",
        )
        batch_op.create_check_constraint(
            "ck_tasks_recovery_buffer_range",
            "recovery_buffer_minutes BETWEEN 0 AND 120",
        )


def downgrade() -> None:
    """Remove deterministic priority inputs from tasks."""
    with op.batch_alter_table("tasks", recreate="always") as batch_op:
        batch_op.drop_constraint(
            "ck_tasks_recovery_buffer_range",
            type_="check",
        )
        batch_op.drop_constraint(
            "ck_tasks_effort_level_range",
            type_="check",
        )
        batch_op.drop_constraint(
            "ck_tasks_task_type_values",
            type_="check",
        )
        batch_op.drop_column("splittable")
        batch_op.drop_column("recovery_buffer_minutes")
        batch_op.drop_column("effort_level")
        batch_op.drop_column("task_type")
