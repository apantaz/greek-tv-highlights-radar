"""Orchestrate isolated ingestion runs for a discovered channel catalog."""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from greek_tv.config import http_max_attempts, http_timeout_seconds, minimum_schedule_records
from greek_tv.models import IngestionStatus
from greek_tv.scraper.channels import Channel
from greek_tv.scraper.client import ScheduleClient
from greek_tv.scraper.schedule import IngestionError, ingest_channel


@dataclass(frozen=True, slots=True)
class ChannelIngestionResult:
    """Summarize one channel attempt within a batch."""

    channel: Channel
    status: IngestionStatus
    run_id: str | None
    records_parsed: int
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class BatchIngestionResult:
    """Summarize all isolated channel attempts for one schedule date."""

    schedule_date: date
    channels: tuple[ChannelIngestionResult, ...]

    @property
    def succeeded(self) -> int:
        return sum(result.status is IngestionStatus.SUCCEEDED for result in self.channels)

    @property
    def failed(self) -> int:
        return sum(result.status is IngestionStatus.FAILED for result in self.channels)

    @property
    def all_succeeded(self) -> bool:
        return self.failed == 0


def ingest_all_schedules(
    *,
    schedule_date: date,
    database_path: Path,
    raw_root: Path,
    client: ScheduleClient | None = None,
    minimum_records: int | None = None,
) -> BatchIngestionResult:
    """Discover once and ingest every channel without propagating channel failures."""
    client = client or ScheduleClient(
        timeout=http_timeout_seconds(),
        max_attempts=http_max_attempts(),
    )
    if minimum_records is None:
        minimum_records = minimum_schedule_records()

    catalog = client.fetch_catalog()
    results: list[ChannelIngestionResult] = []
    for channel in catalog:
        try:
            run = ingest_channel(
                channel=channel,
                schedule_date=schedule_date,
                database_path=database_path,
                raw_root=raw_root,
                client=client,
                minimum_records=minimum_records,
            )
        except IngestionError as error:
            cause = error.cause
            results.append(
                ChannelIngestionResult(
                    channel=channel,
                    status=IngestionStatus.FAILED,
                    run_id=error.run_id,
                    records_parsed=0,
                    error_message=f"{type(cause).__name__}: {cause}",
                )
            )
        except Exception as error:
            results.append(
                ChannelIngestionResult(
                    channel=channel,
                    status=IngestionStatus.FAILED,
                    run_id=None,
                    records_parsed=0,
                    error_message=f"{type(error).__name__}: {error}",
                )
            )
        else:
            results.append(
                ChannelIngestionResult(
                    channel=channel,
                    status=IngestionStatus.SUCCEEDED,
                    run_id=run.run_id,
                    records_parsed=run.records_parsed,
                )
            )

    return BatchIngestionResult(schedule_date=schedule_date, channels=tuple(results))
