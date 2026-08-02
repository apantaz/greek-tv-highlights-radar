from datetime import UTC, date, datetime, timedelta

import duckdb

from greek_tv.database import IngestionRepository
from greek_tv.models import Broadcast, IngestionRun, IngestionStatus

SOURCE_URL = "https://programmatileorasis.gr/free/18/ΕΡΤ1?date=2026-07-19"


def broadcast(title: str, retrieved_at: datetime) -> Broadcast:
    return Broadcast(
        channel="ΕΡΤ1",
        title=title,
        starts_at=datetime(2026, 7, 19, 20, tzinfo=UTC),
        ends_at=datetime(2026, 7, 19, 21, tzinfo=UTC),
        source_url=SOURCE_URL,
        retrieved_at=retrieved_at,
    )


def run(run_id: str, started_at: datetime) -> IngestionRun:
    return IngestionRun(
        run_id=run_id,
        source="programmatileorasis",
        channel="ΕΡΤ1",
        schedule_date=date(2026, 7, 19),
        source_url=SOURCE_URL,
        started_at=started_at,
        status=IngestionStatus.RUNNING,
    )


def test_preserves_observations_while_current_view_uses_latest_run(tmp_path):
    repository = IngestionRepository(tmp_path / "test.duckdb")
    first_time = datetime(2026, 7, 19, 10, tzinfo=UTC)
    second_time = first_time + timedelta(hours=1)
    repository.start_run(run("run-1", first_time))
    repository.complete_run(
        "run-1", [broadcast("Original", first_time)], tmp_path / "1.html", first_time
    )
    repository.start_run(run("run-2", second_time))
    repository.complete_run(
        "run-2", [broadcast("Changed", second_time)], tmp_path / "2.html", second_time
    )

    assert repository.count("ingestion_runs") == 2
    assert repository.count("broadcast_observations") == 2
    assert repository.count("current_broadcasts") == 1
    with duckdb.connect(str(repository.path), read_only=True) as connection:
        assert connection.execute("select title from current_broadcasts").fetchone()[0] == "Changed"


def test_records_failed_run_without_observations(tmp_path):
    repository = IngestionRepository(tmp_path / "test.duckdb")
    started_at = datetime(2026, 7, 19, 10, tzinfo=UTC)
    repository.start_run(run("failed-run", started_at))

    repository.fail_run("failed-run", ValueError("bad schedule"), started_at)

    failed = repository.get_run("failed-run")
    assert failed.status is IngestionStatus.FAILED
    assert failed.error_message == "ValueError: bad schedule"
    assert repository.count("broadcast_observations") == 0


def test_failed_run_does_not_replace_latest_successful_schedule(tmp_path):
    repository = IngestionRepository(tmp_path / "test.duckdb")
    first_time = datetime(2026, 7, 19, 10, tzinfo=UTC)
    repository.start_run(run("successful-run", first_time))
    repository.complete_run(
        "successful-run",
        [broadcast("Trusted", first_time)],
        tmp_path / "success.html",
        first_time,
    )
    repository.start_run(run("later-failed-run", first_time + timedelta(hours=1)))
    repository.fail_run(
        "later-failed-run",
        ValueError("upstream changed"),
        first_time + timedelta(hours=1),
    )

    with duckdb.connect(str(repository.path), read_only=True) as connection:
        assert connection.execute("select title from current_broadcasts").fetchone()[0] == "Trusted"


def test_migrates_legacy_broadcasts_without_dropping_original_table(tmp_path):
    path = tmp_path / "legacy.duckdb"
    item = broadcast("Legacy title", datetime(2026, 7, 19, 10, tzinfo=UTC))
    with duckdb.connect(str(path)) as connection:
        connection.execute(
            """
            create table broadcasts (
                broadcast_id varchar primary key,
                channel varchar not null,
                title varchar not null,
                starts_at timestamptz not null,
                ends_at timestamptz,
                description varchar,
                source_url varchar not null,
                retrieved_at timestamptz not null
            )
            """
        )
        connection.execute(
            "insert into broadcasts values (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                item.broadcast_id,
                item.channel,
                item.title,
                item.starts_at,
                item.ends_at,
                item.description,
                item.source_url,
                item.retrieved_at,
            ],
        )

    repository = IngestionRepository(path)
    repository.initialize()
    repository.initialize()

    assert repository.count("ingestion_runs") == 1
    assert repository.count("broadcast_observations") == 1
    assert repository.count("current_broadcasts") == 1
    with duckdb.connect(str(path), read_only=True) as connection:
        assert connection.execute("select count(*) from broadcasts").fetchone()[0] == 1
