"""Persistent lineage between schedule observations and enrichment lookups."""

from datetime import UTC, datetime
from pathlib import Path

import duckdb


class BroadcastEnrichmentLineageRepository:
    """Persist idempotent observation-to-lookup relationships."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def initialize(self) -> None:
        with duckdb.connect(str(self.path)) as connection:
            connection.execute(
                """
                create table if not exists broadcast_enrichment_lookups (
                    observation_id varchar not null,
                    lookup_id varchar not null,
                    language varchar not null,
                    scoring_version varchar not null,
                    linked_at timestamptz not null,
                    primary key (observation_id, lookup_id, scoring_version),
                    foreign key (observation_id)
                        references broadcast_observations(observation_id),
                    foreign key (lookup_id) references tmdb_lookup_contexts(lookup_id)
                )
                """
            )

    def link(
        self,
        observation_ids: tuple[str, ...],
        lookup_id: str,
        language: str,
        *,
        scoring_version: str = "v1",
        linked_at: datetime | None = None,
    ) -> None:
        """Link observations to a lookup without duplicating existing lineage."""
        if not observation_ids:
            return
        linked_at = linked_at or datetime.now(UTC)
        if linked_at.tzinfo is None:
            raise ValueError("lineage timestamp must be timezone-aware")
        self.initialize()
        with duckdb.connect(str(self.path)) as connection:
            connection.executemany(
                """
                insert into broadcast_enrichment_lookups
                values (?, ?, ?, ?, ?)
                on conflict do nothing
                """,
                [
                    (observation_id, lookup_id, language, scoring_version, linked_at)
                    for observation_id in observation_ids
                ],
            )
