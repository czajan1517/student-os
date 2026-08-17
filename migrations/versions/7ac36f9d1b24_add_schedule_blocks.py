"""add task-linked schedule blocks

Revision ID: 7ac36f9d1b24
Revises: 408005d2614a
Create Date: 2026-08-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7ac36f9d1b24"
down_revision: Union[str, Sequence[str], None] = "408005d2614a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the relationship and scheduling behavior to calendar events."""
    with op.batch_alter_table(
        "calendar_events",
        recreate="always",
    ) as batch_op:
        batch_op.add_column(
            sa.Column("task_id", sa.Integer(), nullable=True),
        )
        batch_op.add_column(
            sa.Column(
                "locked",
                sa.Boolean(),
                server_default=sa.text("1"),
                nullable=False,
            ),
        )
        batch_op.add_column(
            sa.Column(
                "buffer_after_minutes",
                sa.Integer(),
                server_default=sa.text("0"),
                nullable=False,
            ),
        )
        batch_op.create_foreign_key(
            "fk_calendar_events_task_id_tasks",
            "tasks",
            ["task_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_index(
            "ix_calendar_events_task_id",
            ["task_id"],
            unique=False,
        )
        batch_op.create_check_constraint(
            "ck_calendar_events_buffer_range",
            "buffer_after_minutes BETWEEN 0 AND 240",
        )


def downgrade() -> None:
    """Remove task-linked schedule block fields."""
    with op.batch_alter_table(
        "calendar_events",
        recreate="always",
    ) as batch_op:
        batch_op.drop_constraint(
            "ck_calendar_events_buffer_range",
            type_="check",
        )
        batch_op.drop_index("ix_calendar_events_task_id")
        batch_op.drop_constraint(
            "fk_calendar_events_task_id_tasks",
            type_="foreignkey",
        )
        batch_op.drop_column("buffer_after_minutes")
        batch_op.drop_column("locked")
        batch_op.drop_column("task_id")
