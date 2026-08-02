"""Orchestrate one auditable schedule ingestion run."""

from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

from greek_tv.config import http_max_attempts, http_timeout_seconds, minimum_schedule_records
from greek_tv.database import IngestionRepository
from greek_tv.ingestion.quality import validate_schedule
from greek_tv.models import IngestionRun, IngestionStatus
from greek_tv.scraper.client import CHANNELS, SOURCE_NAME, ScheduleClient, save_snapshot
from greek_tv.scraper.parser import parse_schedule


class IngestionError(RuntimeError):
    """Expose the failed run identifier while retaining the original cause."""

    def __init__(self, run_id: str, cause: Exception) -> None:
        super().__init__(f"ingestion run {run_id} failed: {cause}")
        self.run_id = run_id
        self.cause = cause


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _run_id() -> str:
    return uuid4().hex


def ingest_schedule(
    *,
    channel: str,
    schedule_date: date,
    database_path: Path,
    raw_root: Path,
    client: ScheduleClient | None = None,
    minimum_records: int | None = None,
    clock: Callable[[], datetime] = _utc_now,
    run_id_factory: Callable[[], str] = _run_id,
) -> IngestionRun:
    """Fetch, snapshot, validate, and persist one channel/date schedule."""
    normalized_channel = channel.lower()
    try:
        channel_id, channel_name = CHANNELS[normalized_channel]
    except KeyError as error:
        supported = ", ".join(sorted(CHANNELS))
        raise ValueError(f"unsupported channel {channel!r}; choose one of: {supported}") from error

    client = client or ScheduleClient(
        timeout=http_timeout_seconds(),
        max_attempts=http_max_attempts(),
    )
    if minimum_records is None:
        minimum_records = minimum_schedule_records()
    repository = IngestionRepository(database_path)
    run_id = run_id_factory()
    source_url = client.source_url(normalized_channel, schedule_date)
    started_at = clock()
    run = IngestionRun(
        run_id=run_id,
        source=SOURCE_NAME,
        channel=channel_name,
        schedule_date=schedule_date,
        source_url=source_url,
        started_at=started_at,
        status=IngestionStatus.RUNNING,
    )
    repository.start_run(run)

    snapshot_path: Path | None = None
    try:
        html, response_url = client.fetch(normalized_channel, schedule_date)
        snapshot_path = save_snapshot(
            html,
            raw_root,
            normalized_channel,
            schedule_date,
            run_id,
        )
        retrieved_at = clock()
        broadcasts = parse_schedule(
            html,
            channel_id=channel_id,
            channel=channel_name,
            schedule_date=schedule_date,
            source_url=response_url,
            retrieved_at=retrieved_at,
        )
        validate_schedule(broadcasts, minimum_records)
        repository.complete_run(run_id, broadcasts, snapshot_path, clock())
    except Exception as error:
        repository.fail_run(run_id, error, clock(), snapshot_path)
        raise IngestionError(run_id, error) from error

    return repository.get_run(run_id)
