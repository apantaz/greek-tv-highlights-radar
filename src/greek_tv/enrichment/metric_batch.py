"""Bounded refreshes for historical TMDB popularity and voting metrics."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path

from greek_tv.enrichment.entities import TmdbEntityRepository
from greek_tv.enrichment.tmdb import TmdbClient


def _utc_now() -> datetime:
    return datetime.now(UTC)


class MetricSnapshotStatus(StrEnum):
    """Outcome of one entity metric-snapshot operation."""

    FRESH = "fresh"
    SNAPSHOTTED = "snapshotted"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class MetricSnapshotResult:
    """Outcome for one cached TMDB identity."""

    media_type: str
    tmdb_id: int
    status: MetricSnapshotStatus
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class BatchMetricSnapshotResult:
    """Aggregate result for one bounded metric refresh."""

    entities: tuple[MetricSnapshotResult, ...]

    @property
    def total(self) -> int:
        return len(self.entities)

    def count(self, status: MetricSnapshotStatus) -> int:
        return sum(item.status is status for item in self.entities)

    @property
    def failed(self) -> int:
        return self.count(MetricSnapshotStatus.FAILED)


def snapshot_entity_metrics(
    database_path: Path,
    *,
    language: str,
    max_age_hours: float,
    client_factory: Callable[[], TmdbClient],
    limit: int | None = None,
    clock: Callable[[], datetime] = _utc_now,
) -> BatchMetricSnapshotResult:
    """Append metrics only when an entity's newest observation exceeds the max age."""
    if max_age_hours < 0:
        raise ValueError("metric maximum age must not be negative")
    if limit is not None and limit < 1:
        raise ValueError("metric snapshot limit must be at least 1")
    repository = TmdbEntityRepository(database_path)
    identities = repository.detailed_identities()
    if limit is not None:
        identities = identities[:limit]
    now = clock()
    if now.tzinfo is None:
        raise ValueError("metric snapshot clock must be timezone-aware")
    cutoff = now - timedelta(hours=max_age_hours)
    results = []
    client = None
    for media_type, tmdb_id in identities:
        try:
            latest = repository.latest_metric(media_type, tmdb_id)
            if latest is not None and latest.observed_at > cutoff:
                results.append(
                    MetricSnapshotResult(media_type, tmdb_id, MetricSnapshotStatus.FRESH)
                )
                continue
            if client is None:
                client = client_factory()
            details = client.details(media_type, tmdb_id, language)
            repository.save(details, retrieved_at=now)
            results.append(
                MetricSnapshotResult(media_type, tmdb_id, MetricSnapshotStatus.SNAPSHOTTED)
            )
        except Exception as error:
            results.append(
                MetricSnapshotResult(
                    media_type,
                    tmdb_id,
                    MetricSnapshotStatus.FAILED,
                    f"{type(error).__name__}: {error}"[:2000],
                )
            )
    return BatchMetricSnapshotResult(tuple(results))
