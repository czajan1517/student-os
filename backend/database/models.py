from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime



class Base(DeclarativeBase):
    pass

class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "priority IN (0, 1, 2, 3)",
            name="ck_tasks_priority_range",
        ),
        CheckConstraint(
            "estimated_time > 0",
            name="ck_tasks_estimated_time_positive",
        ),
        CheckConstraint(
            "task_type IN ('general', 'assignment', 'exam_preparation', "
            "'project', 'study', 'admin', 'chore', 'personal')",
            name="ck_tasks_task_type_values",
        ),
        CheckConstraint(
            "effort_level IN (0, 1, 2)",
            name="ck_tasks_effort_level_range",
        ),
        CheckConstraint(
            "recovery_buffer_minutes BETWEEN 0 AND 120",
            name="ck_tasks_recovery_buffer_range",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    description: Mapped[str] = mapped_column(
        String(2000),
        default="",
        server_default=text("''"),
        nullable=False,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
    )

    estimated_time: Mapped[int] = mapped_column(
        Integer,
        default=60,
        server_default=text("60"),
        nullable=False,
    )

    task_type: Mapped[str] = mapped_column(
        String(32),
        default="general",
        server_default=text("'general'"),
        nullable=False,
    )

    effort_level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default=text("1"),
        nullable=False,
    )

    recovery_buffer_minutes: Mapped[int] = mapped_column(
        Integer,
        default=15,
        server_default=text("15"),
        nullable=False,
    )

    splittable: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("1"),
        nullable=False,
    )

    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("0"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now,
        onupdate=datetime.now
        )

    scheduled_events: Mapped[list["CalendarEvent"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
    )


class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    __table_args__ = (
        CheckConstraint(
            "priority IN (0, 1, 2, 3)",
            name="ck_calendar_events_priority_range",
        ),
        CheckConstraint(
            "end_date > start_date",
            name="ck_calendar_events_date_order",
        ),
        CheckConstraint(
            "buffer_after_minutes BETWEEN 0 AND 240",
            name="ck_calendar_events_buffer_range",
        ),
    )


    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    description: Mapped[str] = mapped_column(
        String(2000),
        default="",
        server_default=text("''"),
        nullable=False,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
    )

    # Distinguishes standalone events (None) from time blocks linked to tasks.
    task_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )

    locked: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("1"),
        nullable=False,
    )

    buffer_after_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
    )

    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    task: Mapped[Task | None] = relationship(back_populates="scheduled_events")
