from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
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

    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
