"""Unattended metadata retrieval for confidently matched TMDB identities."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path

from greek_tv.enrichment.entities import TmdbEntityRepository
from greek_tv.enrichment.repository import TmdbCandidateRepository
from greek_tv.enrichment.tmdb import TmdbClient


class EntityEnrichmentStatus(StrEnum):
    """Outcome of one matched-identity metadata operation."""

    CACHED = "cached"
    RETRIEVED = "retrieved"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class EntityEnrichmentResult:
    """Outcome for one accepted TMDB identity."""

    media_type: str
    tmdb_id: int
    status: EntityEnrichmentStatus
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class BatchEntityEnrichmentResult:
    """Aggregate result for one matched-entity metadata pass."""

    entities: tuple[EntityEnrichmentResult, ...]

    @property
    def total(self) -> int:
        return len(self.entities)

    def count(self, status: EntityEnrichmentStatus) -> int:
        return sum(item.status is status for item in self.entities)

    @property
    def failed(self) -> int:
        return self.count(EntityEnrichmentStatus.FAILED)


def enrich_matched_entities(
    database_path: Path,
    *,
    language: str,
    client_factory: Callable[[], TmdbClient],
    limit: int | None = None,
    refresh: bool = False,
    schedule_date: date | None = None,
    on_entity: Callable[[EntityEnrichmentResult, int, int], None] | None = None,
) -> BatchEntityEnrichmentResult:
    """Retrieve or reuse details for every distinct confidently matched identity."""
    if limit is not None and limit < 1:
        raise ValueError("entity enrichment limit must be at least 1")
    TmdbCandidateRepository(database_path).initialize()
    repository = TmdbEntityRepository(database_path)
    identities = repository.matched_identities(schedule_date=schedule_date)
    if limit is not None:
        identities = identities[:limit]
    total_entities = len(identities)
    results = []
    client = None
    for media_type, tmdb_id in identities:
        try:
            cached = repository.latest(media_type, tmdb_id, language)
            if cached is not None and not refresh:
                result = EntityEnrichmentResult(media_type, tmdb_id, EntityEnrichmentStatus.CACHED)
                results.append(result)
                if on_entity is not None:
                    on_entity(result, len(results), total_entities)
                continue
            if client is None:
                client = client_factory()
            details = client.details(media_type, tmdb_id, language)
            repository.save(details)
            result = EntityEnrichmentResult(media_type, tmdb_id, EntityEnrichmentStatus.RETRIEVED)
        except Exception as error:
            result = EntityEnrichmentResult(
                media_type,
                tmdb_id,
                EntityEnrichmentStatus.FAILED,
                f"{type(error).__name__}: {error}"[:2000],
            )
        results.append(result)
        if on_entity is not None:
            on_entity(result, len(results), total_entities)
    return BatchEntityEnrichmentResult(tuple(results))
