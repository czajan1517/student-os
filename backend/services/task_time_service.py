import re
from datetime import date, datetime, time, timedelta
from typing import Callable

import dateparser

from backend.schemas.schedule import (
    TaskScheduleIntent,
    TaskTimingParseResult,
)


class TaskTimeService:
    """Extract explicit task deadlines and fixed schedule requests."""

    _TIME_TOKEN = (
        r"(?:midnight|noon|"
        r"\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?))"
    )
    _DATE_TOKEN = (
        r"(?:today|tomorrow|\d{4}-\d{2}-\d{2}|"
        r"\d{1,2}/\d{1,2}/\d{4}|"
        r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
        r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|"
        r"oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
        r"\s+\d{1,2}(?:,?\s+\d{4})?)"
    )

    def __init__(
        self,
        *,
        now_factory: Callable[[], datetime] | None = None,
    ):
        self._now_factory = now_factory or (
            lambda: datetime.now().astimezone()
        )

    def parse(self, message: str) -> TaskTimingParseResult:
        now = self._now_factory()
        duration_minutes = self._parse_duration_minutes(message)
        explicit_date = self._parse_date(message, now)
        has_schedule_start = self._has_schedule_start(message)
        has_deadline = self._has_deadline(message, has_schedule_start)

        deadline_result = None
        if has_deadline:
            deadline_result = self._build_deadline_result(
                message=message,
                now=now,
                explicit_date=explicit_date,
                duration_minutes=duration_minutes,
            )

        start_time = self._parse_start_time(message)
        end_time = self._parse_end_time(message)
        has_schedule_request = has_schedule_start or (
            not has_deadline
            and (start_time is not None or end_time is not None)
        )
        if not has_schedule_request:
            if deadline_result is not None:
                return deadline_result
            return TaskTimingParseResult(
                duration_minutes=duration_minutes,
            )

        questions = (
            list(deadline_result.clarification_questions)
            if deadline_result is not None
            else []
        )
        if start_time is None:
            questions.append(
                "What time should this scheduled task start?"
            )
        if explicit_date is None:
            questions.append(
                "What date should this scheduled task occur?"
            )
        if duration_minutes is None and end_time is None:
            questions.append(
                "How long should this scheduled task take?"
            )

        schedule = None
        if start_time is not None and explicit_date is not None:
            schedule, schedule_question = self._resolve_schedule(
                now=now,
                schedule_date=explicit_date,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=duration_minutes,
            )
            if schedule_question is not None:
                questions.append(schedule_question)
            elif (
                schedule is not None
                and deadline_result is not None
                and deadline_result.due_date is not None
                and schedule.end_at > deadline_result.due_date
            ):
                questions.append(
                    "The requested schedule ends after the task deadline. "
                    "What should StudentOS change?"
                )

        return TaskTimingParseResult(
            due_date=(
                deadline_result.due_date
                if deadline_result is not None
                else None
            ),
            requested_schedule_date=explicit_date,
            requested_start_time=start_time,
            requested_end_time=end_time,
            duration_minutes=duration_minutes,
            schedule=schedule if not questions else None,
            clarification_questions=questions,
        )

    def _build_deadline_result(
        self,
        *,
        message: str,
        now: datetime,
        explicit_date: date | None,
        duration_minutes: int | None,
    ) -> TaskTimingParseResult:
        deadline_time = self._parse_deadline_time(message)
        questions: list[str] = []
        if explicit_date is None:
            questions.append("What date should this task be due?")
        if deadline_time is None:
            questions.append("What time should this task be due?")

        due_date = None
        if explicit_date is not None and deadline_time is not None:
            due_date = self._combine(
                explicit_date,
                deadline_time,
                now,
            )

        return TaskTimingParseResult(
            due_date=due_date,
            duration_minutes=duration_minutes,
            clarification_questions=questions,
        )

    def _resolve_schedule(
        self,
        *,
        now: datetime,
        schedule_date: date,
        start_time: time,
        end_time: time | None,
        duration_minutes: int | None,
    ) -> tuple[TaskScheduleIntent | None, str | None]:
        start_at = self._combine(schedule_date, start_time, now)

        if end_time is not None:
            end_at = self._combine(schedule_date, end_time, now)
            if end_at <= start_at:
                end_at += timedelta(days=1)
            explicit_minutes = round(
                (end_at - start_at).total_seconds() / 60
            )
            if (
                duration_minutes is not None
                and explicit_minutes != duration_minutes
            ):
                return (
                    None,
                    "The requested end time and duration do not match. "
                    "Which one should StudentOS use?",
                )
        elif duration_minutes is not None:
            end_at = start_at + timedelta(minutes=duration_minutes)
        else:
            return None, None

        return (
            TaskScheduleIntent(
                start_at=start_at,
                end_at=end_at,
                locked=True,
            ),
            None,
        )

    @classmethod
    def _parse_duration_minutes(cls, message: str) -> int | None:
        hours = re.search(
            r"\b(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|hr)\b",
            message,
            flags=re.IGNORECASE,
        )
        if hours:
            minutes = round(float(hours.group(1)) * 60)
            return minutes if 0 < minutes <= 1440 else None

        minutes = re.search(
            r"\b(\d+)\s*(?:minutes?|mins?|min)\b",
            message,
            flags=re.IGNORECASE,
        )
        if minutes:
            value = int(minutes.group(1))
            return value if 0 < value <= 1440 else None
        return None

    @classmethod
    def _parse_date(cls, message: str, now: datetime) -> date | None:
        match = re.search(cls._DATE_TOKEN, message, flags=re.IGNORECASE)
        if not match:
            return None

        parsed = dateparser.parse(
            match.group(0),
            settings={
                "RELATIVE_BASE": now.replace(tzinfo=None),
                "PREFER_DATES_FROM": "future",
                "STRICT_PARSING": True,
            },
        )
        return parsed.date() if parsed is not None else None

    @classmethod
    def _parse_start_time(cls, message: str) -> time | None:
        patterns = (
            rf"\b(?:start|starting|begin|beginning)\b.*?\bat\s+"
            rf"(?P<clock>{cls._TIME_TOKEN})",
            rf"\b{cls._DATE_TOKEN}\s+at\s+"
            rf"(?P<clock>{cls._TIME_TOKEN})",
        )
        for pattern in patterns:
            match = re.search(pattern, message, flags=re.IGNORECASE)
            if match:
                return cls._parse_time_token(match.group("clock"))
        return None

    @classmethod
    def _parse_end_time(cls, message: str) -> time | None:
        pattern = (
            rf"\b(?:end|ending|until|finish)\b(?:\s+at|\s+by)?\s+"
            rf"(?P<clock>{cls._TIME_TOKEN})"
        )
        match = re.search(pattern, message, flags=re.IGNORECASE)
        return (
            cls._parse_time_token(match.group("clock"))
            if match
            else None
        )

    @classmethod
    def _parse_deadline_time(cls, message: str) -> time | None:
        patterns = (
            rf"\b(?:due|deadline)\b(?:\s+(?:is|on))?\s*"
            rf"(?:{cls._DATE_TOKEN}\s+)?"
            rf"(?:at|by|is)\s+(?P<clock>{cls._TIME_TOKEN})",
            rf"\b(?:finish|complete|submit)\b[^.;\n]*?\bby\s+"
            rf"(?:{cls._DATE_TOKEN}\s+)?(?:at\s+)?"
            rf"(?P<clock>{cls._TIME_TOKEN})",
        )
        for pattern in patterns:
            match = re.search(pattern, message, flags=re.IGNORECASE)
            if match:
                return cls._parse_time_token(match.group("clock"))
        return None

    @staticmethod
    def _parse_time_token(value: str) -> time | None:
        normalized = re.sub(r"[.\s]", "", value).lower()
        if normalized == "midnight":
            return time(0, 0)
        if normalized == "noon":
            return time(12, 0)

        match = re.fullmatch(
            r"(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?"
            r"(?P<meridiem>am|pm)",
            normalized,
        )
        if match is None:
            return None

        hour = int(match.group("hour"))
        minute = int(match.group("minute") or 0)
        if not 1 <= hour <= 12 or not 0 <= minute <= 59:
            return None
        if match.group("meridiem") == "am":
            hour = 0 if hour == 12 else hour
        else:
            hour = 12 if hour == 12 else hour + 12
        return time(hour, minute)

    @staticmethod
    def _combine(
        calendar_date: date,
        clock_time: time,
        now: datetime,
    ) -> datetime:
        combined = datetime.combine(calendar_date, clock_time)
        return (
            combined.replace(tzinfo=now.tzinfo)
            if now.tzinfo is not None
            else combined
        )

    @staticmethod
    def _has_schedule_start(message: str) -> bool:
        return bool(
            re.search(
                r"\b(?:start|starting|begin|beginning)\b",
                message,
                flags=re.IGNORECASE,
            )
        )

    @staticmethod
    def _has_deadline(message: str, has_schedule_start: bool) -> bool:
        if re.search(r"\b(?:due|deadline)\b", message, re.IGNORECASE):
            return True
        if has_schedule_start:
            return False
        return bool(
            re.search(
                r"\b(?:finish|complete|submit)\b.*?\bby\b",
                message,
                flags=re.IGNORECASE,
            )
        )
