from datetime import UTC, datetime, timedelta

import pytest

from greek_tv.ingestion.quality import ScheduleQualityError, validate_schedule
from greek_tv.models import Broadcast


def broadcast(title: str, start: datetime) -> Broadcast:
    return Broadcast(
        channel="ΕΡΤ1",
        title=title,
        starts_at=start,
        ends_at=start + timedelta(hours=1),
        source_url="https://example.test/schedule",
        retrieved_at=datetime(2026, 7, 19, tzinfo=UTC),
    )


def test_accepts_chronological_schedule_meeting_threshold():
    start = datetime(2026, 7, 19, 10, tzinfo=UTC)

    validate_schedule([broadcast("One", start), broadcast("Two", start + timedelta(hours=1))], 2)


def test_rejects_schedule_below_minimum_record_threshold():
    item = broadcast("Only", datetime(2026, 7, 19, 10, tzinfo=UTC))

    with pytest.raises(ScheduleQualityError, match="expected at least 2"):
        validate_schedule([item], 2)


def test_rejects_duplicate_start_times():
    start = datetime(2026, 7, 19, 10, tzinfo=UTC)

    with pytest.raises(ScheduleQualityError, match="duplicate start times"):
        validate_schedule([broadcast("One", start), broadcast("Two", start)], 2)


def test_rejects_non_chronological_schedule():
    start = datetime(2026, 7, 19, 10, tzinfo=UTC)

    with pytest.raises(ScheduleQualityError, match="chronological"):
        validate_schedule(
            [broadcast("Later", start + timedelta(hours=1)), broadcast("Earlier", start)], 2
        )
