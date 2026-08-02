"""Data-quality checks applied before schedule observations are persisted."""

from collections.abc import Sequence

from greek_tv.models import Broadcast


class ScheduleQualityError(ValueError):
    """Raised when a parsed schedule is structurally suspicious."""


def validate_schedule(broadcasts: Sequence[Broadcast], minimum_records: int = 5) -> None:
    """Reject empty, undersized, duplicate, or non-chronological schedules."""
    if minimum_records < 1:
        raise ValueError("minimum_records must be at least 1")
    if len(broadcasts) < minimum_records:
        raise ScheduleQualityError(
            f"schedule contains {len(broadcasts)} records; expected at least {minimum_records}"
        )

    starts = [broadcast.starts_at for broadcast in broadcasts]
    if len(starts) != len(set(starts)):
        raise ScheduleQualityError("schedule contains duplicate start times")
    if starts != sorted(starts):
        raise ScheduleQualityError("schedule is not in chronological order")

    for broadcast in broadcasts:
        if broadcast.ends_at is not None and broadcast.ends_at <= broadcast.starts_at:
            raise ScheduleQualityError(
                f"programme {broadcast.title!r} ends before or at its start time"
            )
