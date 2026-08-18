from datetime import datetime
from math import ceil
from typing import Iterable, Mapping

from backend.database.models import Task
from backend.schemas.common import EffortLevel, PriorityLevel, TaskType
from backend.schemas.priority import PriorityAnalysis, PriorityScoreBreakdown


class PriorityService:
    """Rank flexible, incomplete tasks after hard constraints are handled."""

    _IMPORTANCE_POINTS = {
        PriorityLevel.HIGH: 40,
        PriorityLevel.MEDIUM: 30,
        PriorityLevel.NORMAL: 20,
        PriorityLevel.LOW: 10,
    }
    _TASK_TYPE_POINTS = {
        TaskType.EXAM_PREPARATION: 15,
        TaskType.ASSIGNMENT: 12,
        TaskType.PROJECT: 10,
        TaskType.STUDY: 8,
        TaskType.PERSONAL: 7,
        TaskType.GENERAL: 6,
        TaskType.ADMIN: 5,
        TaskType.CHORE: 3,
    }
    _EFFORT_POINTS = {
        EffortLevel.HEAVY: 10,
        EffortLevel.MODERATE: 6,
        EffortLevel.LIGHT: 3,
    }

    def analyze_task(
        self,
        task: Task,
        *,
        scheduled_minutes: int = 0,
        now: datetime | None = None,
    ) -> PriorityAnalysis:
        if task.completed:
            raise ValueError("Completed tasks are not eligible for priority analysis")
        if scheduled_minutes < 0:
            raise ValueError("Scheduled minutes cannot be negative")

        task_type = TaskType(task.task_type)
        effort_level = EffortLevel(task.effort_level)
        importance = PriorityLevel(task.priority)
        remaining_minutes = max(0, task.estimated_time - scheduled_minutes)
        effective_workload_minutes = remaining_minutes
        if remaining_minutes:
            effective_workload_minutes += task.recovery_buffer_minutes

        reference_time = now or self._now_for(task.created_at)
        self._require_matching_timezone_style(reference_time, task.created_at)
        age_days = max(0, (reference_time - task.created_at).days)

        importance_points = self._IMPORTANCE_POINTS[importance]
        task_type_points = self._TASK_TYPE_POINTS[task_type]
        effort_points = self._EFFORT_POINTS[effort_level]
        workload_points = min(10, ceil(effective_workload_minutes / 60) * 2)
        age_points = min(15, age_days)
        total = min(
            100,
            importance_points
            + task_type_points
            + effort_points
            + workload_points
            + age_points,
        )

        breakdown = PriorityScoreBreakdown(
            importance=importance_points,
            task_type=task_type_points,
            effort=effort_points,
            workload=workload_points,
            age=age_points,
            total=total,
        )
        return PriorityAnalysis(
            task_id=task.id,
            task_title=task.title,
            score=total,
            remaining_minutes=remaining_minutes,
            effective_workload_minutes=effective_workload_minutes,
            task_type=task_type,
            effort_level=effort_level,
            splittable=task.splittable,
            recovery_buffer_minutes=task.recovery_buffer_minutes,
            breakdown=breakdown,
            reasons=self._build_reasons(
                importance,
                task_type,
                effort_level,
                remaining_minutes,
                age_days,
            ),
        )

    def rank_tasks(
        self,
        tasks: Iterable[Task],
        *,
        scheduled_minutes_by_task: Mapping[int, int] | None = None,
        now: datetime | None = None,
    ) -> list[PriorityAnalysis]:
        scheduled_minutes_by_task = scheduled_minutes_by_task or {}
        ranked: list[tuple[PriorityAnalysis, datetime, int]] = []

        for task in tasks:
            if task.completed:
                continue
            scheduled_minutes = scheduled_minutes_by_task.get(task.id, 0)
            if scheduled_minutes >= task.estimated_time:
                continue
            analysis = self.analyze_task(
                task,
                scheduled_minutes=scheduled_minutes,
                now=now,
            )
            ranked.append((analysis, task.created_at, task.id))

        ranked.sort(
            key=lambda item: (
                -item[0].score,
                self._sortable_datetime(item[1]),
                item[2],
            )
        )
        return [analysis for analysis, _created_at, _task_id in ranked]

    @staticmethod
    def _build_reasons(
        importance: PriorityLevel,
        task_type: TaskType,
        effort_level: EffortLevel,
        remaining_minutes: int,
        age_days: int,
    ) -> list[str]:
        reasons = [
            f"User importance is {importance.name.lower()}",
            f"Task type is {task_type.value.replace('_', ' ')}",
            f"Effort level is {effort_level.name.lower()}",
            f"{remaining_minutes} minutes remain to allocate",
        ]
        if age_days:
            reasons.append(f"Task has waited {age_days} day(s)")
        return reasons

    @staticmethod
    def _now_for(created_at: datetime) -> datetime:
        return datetime.now(tz=created_at.tzinfo)

    @staticmethod
    def _require_matching_timezone_style(first: datetime, second: datetime) -> None:
        if (first.utcoffset() is None) != (second.utcoffset() is None):
            raise ValueError("Priority timestamps must use the same timezone style")

    @staticmethod
    def _sortable_datetime(value: datetime) -> float:
        if value.utcoffset() is None:
            return value.replace(tzinfo=None).timestamp()
        return value.timestamp()
