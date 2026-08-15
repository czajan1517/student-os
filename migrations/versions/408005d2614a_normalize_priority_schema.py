"""normalize priority schema

Revision ID: 408005d2614a
Revises: 25b9c5e2c8ce
Create Date: 2026-08-15 17:00:13.621089

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '408005d2614a'
down_revision: Union[str, Sequence[str], None] = '25b9c5e2c8ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "UPDATE tasks SET priority = '0' "
        "WHERE priority IS NULL "
        "OR CAST(priority AS INTEGER) NOT BETWEEN 0 AND 3"
    )
    op.execute(
        "UPDATE tasks SET estimated_time = 60 "
        "WHERE estimated_time IS NULL OR estimated_time <= 0"
    )
    op.execute(
        "UPDATE calendar_events SET priority = 0 "
        "WHERE priority IS NULL OR priority NOT BETWEEN 0 AND 3"
    )

    with op.batch_alter_table("tasks", recreate="always") as batch_op:
        batch_op.alter_column(
            "title",
            existing_type=sa.String(),
            type_=sa.String(length=200),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "description",
            existing_type=sa.String(),
            type_=sa.String(length=2000),
            existing_nullable=False,
            server_default=sa.text("''"),
        )
        batch_op.alter_column(
            "priority",
            existing_type=sa.String(),
            type_=sa.Integer(),
            existing_nullable=False,
            server_default=sa.text("0"),
        )
        batch_op.alter_column(
            "estimated_time",
            existing_type=sa.Integer(),
            existing_nullable=False,
            server_default=sa.text("60"),
        )
        batch_op.alter_column(
            "completed",
            existing_type=sa.Boolean(),
            existing_nullable=False,
            server_default=sa.text("0"),
        )
        batch_op.create_check_constraint(
            "ck_tasks_priority_range",
            "priority IN (0, 1, 2, 3)",
        )
        batch_op.create_check_constraint(
            "ck_tasks_estimated_time_positive",
            "estimated_time > 0",
        )

    with op.batch_alter_table(
        "calendar_events",
        recreate="always",
    ) as batch_op:
        batch_op.alter_column(
            "title",
            existing_type=sa.String(),
            type_=sa.String(length=200),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "description",
            existing_type=sa.String(),
            type_=sa.String(length=2000),
            existing_nullable=False,
            server_default=sa.text("''"),
        )
        batch_op.alter_column(
            "priority",
            existing_type=sa.Integer(),
            existing_nullable=False,
            server_default=sa.text("0"),
        )
        batch_op.create_check_constraint(
            "ck_calendar_events_priority_range",
            "priority IN (0, 1, 2, 3)",
        )
        batch_op.create_check_constraint(
            "ck_calendar_events_date_order",
            "end_date > start_date",
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table(
        "calendar_events",
        recreate="always",
    ) as batch_op:
        batch_op.drop_constraint(
            "ck_calendar_events_date_order",
            type_="check",
        )
        batch_op.drop_constraint(
            "ck_calendar_events_priority_range",
            type_="check",
        )
        batch_op.alter_column(
            "priority",
            existing_type=sa.Integer(),
            existing_nullable=False,
            server_default=None,
        )
        batch_op.alter_column(
            "description",
            existing_type=sa.String(length=2000),
            type_=sa.String(),
            existing_nullable=False,
            server_default=None,
        )
        batch_op.alter_column(
            "title",
            existing_type=sa.String(length=200),
            type_=sa.String(),
            existing_nullable=False,
        )

    with op.batch_alter_table("tasks", recreate="always") as batch_op:
        batch_op.drop_constraint(
            "ck_tasks_estimated_time_positive",
            type_="check",
        )
        batch_op.drop_constraint(
            "ck_tasks_priority_range",
            type_="check",
        )
        batch_op.alter_column(
            "completed",
            existing_type=sa.Boolean(),
            existing_nullable=False,
            server_default=None,
        )
        batch_op.alter_column(
            "estimated_time",
            existing_type=sa.Integer(),
            existing_nullable=False,
            server_default=None,
        )
        batch_op.alter_column(
            "priority",
            existing_type=sa.Integer(),
            type_=sa.String(),
            existing_nullable=False,
            server_default=None,
        )
        batch_op.alter_column(
            "description",
            existing_type=sa.String(length=2000),
            type_=sa.String(),
            existing_nullable=False,
            server_default=None,
        )
        batch_op.alter_column(
            "title",
            existing_type=sa.String(length=200),
            type_=sa.String(),
            existing_nullable=False,
        )
