from datetime import date

import pytest

from greek_tv.database import IngestionRepository
from greek_tv.ingestion.batch import ingest_all_schedules
from greek_tv.models import IngestionStatus
from greek_tv.scraper.channels import Channel


class BatchClient:
    def __init__(
        self,
        schedule_html: str,
        failing_slugs: set[str] | None = None,
    ) -> None:
        self.schedule_html = schedule_html
        self.failing_slugs = failing_slugs or set()
        self.catalog_calls = 0
        self.fetches: list[str] = []
        self.channels = (
            Channel("ert1", 18, "ΕΡΤ1"),
            Channel("ert2", 87, "ΕΡΤ2"),
            Channel("alpha", 5, "ALPHA"),
        )

    def fetch_catalog(self) -> tuple[Channel, ...]:
        self.catalog_calls += 1
        return self.channels

    def source_url(self, channel: Channel, schedule_date: date) -> str:
        return f"https://example.test/{channel.source_id}?date={schedule_date.isoformat()}"

    def fetch(self, channel: Channel, schedule_date: date) -> tuple[str, str]:
        self.fetches.append(channel.slug)
        if channel.slug in self.failing_slugs:
            raise RuntimeError(f"{channel.slug} unavailable")
        html = self.schedule_html.replace("channel18", f"channel{channel.source_id}")
        return html, self.source_url(channel, schedule_date)


def ingest_batch(tmp_path, schedule_html, client):
    return ingest_all_schedules(
        schedule_date=date(2026, 7, 19),
        database_path=tmp_path / "test.duckdb",
        raw_root=tmp_path / "raw",
        client=client,
        minimum_records=3,
    )


def test_batch_discovers_once_and_ingests_every_channel(tmp_path, schedule_html):
    client = BatchClient(schedule_html)

    result = ingest_batch(tmp_path, schedule_html, client)

    assert client.catalog_calls == 1
    assert client.fetches == ["ert1", "ert2", "alpha"]
    assert result.succeeded == 3
    assert result.failed == 0
    assert result.all_succeeded
    assert all(item.run_id for item in result.channels)
    assert all(item.records_parsed == 3 for item in result.channels)
    repository = IngestionRepository(tmp_path / "test.duckdb")
    assert repository.count("ingestion_runs") == 3
    assert repository.count("broadcast_observations") == 9


def test_batch_isolates_failure_and_continues(tmp_path, schedule_html):
    client = BatchClient(schedule_html, {"ert2"})

    result = ingest_batch(tmp_path, schedule_html, client)

    assert client.fetches == ["ert1", "ert2", "alpha"]
    assert result.succeeded == 2
    assert result.failed == 1
    assert not result.all_succeeded
    failure = result.channels[1]
    assert failure.channel.slug == "ert2"
    assert failure.status is IngestionStatus.FAILED
    assert failure.run_id is not None
    assert failure.error_message == "RuntimeError: ert2 unavailable"
    repository = IngestionRepository(tmp_path / "test.duckdb")
    assert repository.count("ingestion_runs") == 3
    assert repository.count("broadcast_observations") == 6


def test_batch_reports_complete_failure(tmp_path, schedule_html):
    client = BatchClient(schedule_html, {"alpha", "ert1", "ert2"})

    result = ingest_batch(tmp_path, schedule_html, client)

    assert result.succeeded == 0
    assert result.failed == 3
    assert not result.all_succeeded
    assert all(item.status is IngestionStatus.FAILED for item in result.channels)


def test_catalog_failure_prevents_batch_from_starting(tmp_path, schedule_html):
    client = BatchClient(schedule_html)

    def fail_catalog():
        raise RuntimeError("catalog unavailable")

    client.fetch_catalog = fail_catalog

    with pytest.raises(RuntimeError, match="catalog unavailable"):
        ingest_batch(tmp_path, schedule_html, client)

    assert not (tmp_path / "test.duckdb").exists()
