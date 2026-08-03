"""Unattended enrichment of distinct current schedule programmes."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path

import duckdb

from greek_tv.database import IngestionRepository
from greek_tv.enrichment.evidence import extract_title_evidence
from greek_tv.enrichment.lineage import BroadcastEnrichmentLineageRepository
from greek_tv.enrichment.repository import TmdbCandidateRepository
from greek_tv.enrichment.resolution import ResolutionStatus
from greek_tv.enrichment.service import SearchSource, enrich_title
from greek_tv.enrichment.tmdb import TmdbClient


class BatchEnrichmentStatus(StrEnum):
    MATCHED = "matched"
    UNRESOLVED = "unresolved"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ProgrammeEnrichmentResult:
    """Outcome for one distinct source-evidence combination."""

    source_title: str
    status: BatchEnrichmentStatus
    search_source: SearchSource | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class BatchEnrichmentResult:
    """Aggregate result for one unattended enrichment pass."""

    programmes: tuple[ProgrammeEnrichmentResult, ...]

    @property
    def total(self) -> int:
        return len(self.programmes)

    def count(self, status: BatchEnrichmentStatus) -> int:
        return sum(item.status is status for item in self.programmes)

    @property
    def failed(self) -> int:
        return self.count(BatchEnrichmentStatus.FAILED)

    @property
    def cached(self) -> int:
        return sum(item.search_source is SearchSource.CACHED for item in self.programmes)

    @property
    def retrieved(self) -> int:
        return sum(item.search_source is SearchSource.RETRIEVED for item in self.programmes)


def enrich_current_programmes(
    database_path: Path,
    *,
    language: str,
    client_factory: Callable[[], TmdbClient],
    limit: int | None = None,
    channel: str | None = None,
    schedule_date: date | None = None,
) -> BatchEnrichmentResult:
    """Enrich distinct current programme evidence with isolated per-title failures."""
    if limit is not None and limit < 1:
        raise ValueError("batch enrichment limit must be at least 1")
    IngestionRepository(database_path).initialize()
    repository = TmdbCandidateRepository(database_path)
    repository.initialize()
    rows = _current_programmes(database_path, channel=channel, schedule_date=schedule_date)
    groups = _evidence_groups(rows, language)
    if limit is not None:
        groups = groups[:limit]
    results = []
    lineage = BroadcastEnrichmentLineageRepository(database_path)
    for evidence, description, observation_ids in groups:
        source_title = evidence.source_title
        try:
            lookup_id = repository.resolved_lookup_id(evidence, language)
            if lookup_id is not None:
                lineage.link(observation_ids, lookup_id, language)
                results.append(
                    ProgrammeEnrichmentResult(source_title, BatchEnrichmentStatus.SKIPPED)
                )
                continue
            outcome = enrich_title(
                repository,
                source_title,
                description,
                language=language,
                client_factory=client_factory,
            )
            lineage.link(observation_ids, outcome.lookup.lookup_id, language)
            status = (
                BatchEnrichmentStatus.MATCHED
                if outcome.resolution.resolution.status is ResolutionStatus.MATCHED
                else BatchEnrichmentStatus.UNRESOLVED
            )
            results.append(ProgrammeEnrichmentResult(source_title, status, outcome.search_source))
        except Exception as error:
            results.append(
                ProgrammeEnrichmentResult(
                    source_title,
                    BatchEnrichmentStatus.FAILED,
                    error_message=f"{type(error).__name__}: {error}"[:2000],
                )
            )
    return BatchEnrichmentResult(tuple(results))


def _current_programmes(
    database_path: Path,
    *,
    channel: str | None,
    schedule_date: date | None,
) -> list[tuple[str, str, str | None]]:
    predicates = []
    parameters = []
    if channel:
        predicates.append("lower(runs.channel) = lower(?)")
        parameters.append(channel)
    if schedule_date:
        predicates.append("runs.schedule_date = ?")
        parameters.append(schedule_date)
    where_clause = f"where {' and '.join(predicates)}" if predicates else ""
    with duckdb.connect(str(database_path), read_only=True) as connection:
        return connection.execute(
            f"""
            select
                broadcasts.observation_id,
                broadcasts.title,
                broadcasts.description
            from current_broadcasts as broadcasts
            inner join ingestion_runs as runs using (run_id)
            {where_clause}
            order by title, description, observation_id
            """,
            parameters,
        ).fetchall()


def _evidence_groups(rows, language):
    groups = {}
    for observation_id, source_title, description in rows:
        evidence = extract_title_evidence(source_title, description)
        key = (
            evidence.source_title,
            evidence.production_year,
            evidence.query_titles,
            language,
        )
        if key not in groups:
            groups[key] = [evidence, description, []]
        groups[key][2].append(observation_id)
    return [
        (evidence, description, tuple(observation_ids))
        for evidence, description, observation_ids in groups.values()
    ]
