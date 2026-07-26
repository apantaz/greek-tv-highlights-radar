from datetime import UTC, date, datetime

from greek_tv.database import BroadcastRepository
from greek_tv.scraper.parser import parse_schedule


def test_upsert_is_idempotent(tmp_path, schedule_html):
    broadcasts = parse_schedule(
        schedule_html,
        channel_id=18,
        channel="ΕΡΤ1",
        schedule_date=date(2026, 7, 19),
        source_url="https://programmatileorasis.gr/free/18/ΕΡΤ1?date=2026-07-19",
        retrieved_at=datetime(2026, 7, 19, 10, tzinfo=UTC),
    )
    repository = BroadcastRepository(tmp_path / "test.duckdb")

    repository.upsert(broadcasts)
    repository.upsert(broadcasts)

    assert repository.count() == 3
