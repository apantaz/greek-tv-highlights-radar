from datetime import UTC, date, datetime, timedelta

import duckdb
import pytest

from greek_tv.database import IngestionRepository
from greek_tv.models import IngestionStatus
from greek_tv.scraper.schedule import IngestionError, ingest_schedule


class FakeClient:
    def __init__(self, html: str | None = None, error: Exception | None = None) -> None:
        self.html = html
        self.error = error

    def source_url(self, channel: str, schedule_date: date) -> str:
        return f"https://example.test/{channel}?date={schedule_date.isoformat()}"

    def fetch(self, channel: str, schedule_date: date) -> tuple[str, str]:
        if self.error:
            raise self.error
        assert self.html is not None
        return self.html, self.source_url(channel, schedule_date)


def clock(start: datetime):
    current = start

    def now() -> datetime:
        nonlocal current
        result = current
        current += timedelta(seconds=1)
        return result

    return now


def test_successful_run_creates_audit_record_snapshot_and_observations(tmp_path, schedule_html):
    database = tmp_path / "test.duckdb"
    result = ingest_schedule(
        channel="ert1",
        schedule_date=date(2026, 7, 19),
        database_path=database,
        raw_root=tmp_path / "raw",
        client=FakeClient(schedule_html),
        minimum_records=3,
        clock=clock(datetime(2026, 7, 19, 10, tzinfo=UTC)),
        run_id_factory=lambda: "run-success",
    )

    assert result.status is IngestionStatus.SUCCEEDED
    assert result.records_parsed == 3
    assert result.snapshot_path is not None
    assert (tmp_path / "raw/programmatileorasis/ert1/2026-07-19/run-success.html").exists()
    repository = IngestionRepository(database)
    assert repository.count("ingestion_runs") == 1
    assert repository.count("broadcast_observations") == 3
    assert repository.count("current_broadcasts") == 3


def test_repeated_ingestion_retains_each_run_and_snapshot(tmp_path, schedule_html):
    database = tmp_path / "test.duckdb"
    raw_root = tmp_path / "raw"
    identifiers = iter(["run-1", "run-2"])
    kwargs = {
        "channel": "ert1",
        "schedule_date": date(2026, 7, 19),
        "database_path": database,
        "raw_root": raw_root,
        "client": FakeClient(schedule_html),
        "minimum_records": 3,
        "run_id_factory": lambda: next(identifiers),
    }

    ingest_schedule(**kwargs)
    ingest_schedule(**kwargs)

    repository = IngestionRepository(database)
    assert repository.count("ingestion_runs") == 2
    assert repository.count("broadcast_observations") == 6
    assert repository.count("current_broadcasts") == 3
    assert len(list(raw_root.rglob("*.html"))) == 2


def test_fetch_failure_is_recorded(tmp_path):
    database = tmp_path / "test.duckdb"

    with pytest.raises(IngestionError, match="network unavailable") as captured:
        ingest_schedule(
            channel="ert1",
            schedule_date=date(2026, 7, 19),
            database_path=database,
            raw_root=tmp_path / "raw",
            client=FakeClient(error=RuntimeError("network unavailable")),
            minimum_records=3,
            run_id_factory=lambda: "run-failed",
        )

    assert captured.value.run_id == "run-failed"
    failed = IngestionRepository(database).get_run("run-failed")
    assert failed.status is IngestionStatus.FAILED
    assert failed.snapshot_path is None
    assert failed.error_message == "RuntimeError: network unavailable"


def test_quality_failure_retains_snapshot_but_writes_no_observations(tmp_path, schedule_html):
    database = tmp_path / "test.duckdb"

    with pytest.raises(IngestionError, match="expected at least 4"):
        ingest_schedule(
            channel="ert1",
            schedule_date=date(2026, 7, 19),
            database_path=database,
            raw_root=tmp_path / "raw",
            client=FakeClient(schedule_html),
            minimum_records=4,
            run_id_factory=lambda: "run-quality-failed",
        )

    repository = IngestionRepository(database)
    failed = repository.get_run("run-quality-failed")
    assert failed.status is IngestionStatus.FAILED
    assert failed.snapshot_path is not None
    assert repository.count("broadcast_observations") == 0
    with duckdb.connect(str(database), read_only=True) as connection:
        assert connection.execute("select count(*) from current_broadcasts").fetchone()[0] == 0
