"""DuckDB cache for reproducible TMDB candidate searches."""

import json
from dataclasses import astuple, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import duckdb

from greek_tv.enrichment.evidence import TitleEvidence
from greek_tv.enrichment.resolution import (
    Resolution,
    ResolutionStatus,
    resolution_timestamp,
    resolve_candidates,
)
from greek_tv.enrichment.titles import normalize_title
from greek_tv.enrichment.tmdb import TmdbCandidate, TmdbSearchResponse


@dataclass(frozen=True, slots=True)
class CachedTmdbSearch:
    """One cached TMDB request and all supported candidates it returned."""

    search_id: str
    normalized_title: str
    search_query: str
    language: str
    retrieved_at: datetime
    candidates: tuple[TmdbCandidate, ...]


@dataclass(frozen=True, slots=True)
class TmdbLookupContext:
    """Source evidence linked to the TMDB search selected for later scoring."""

    lookup_id: str
    source_title: str
    normalized_source_title: str
    production_year: int | None
    query_titles: tuple[str, ...]
    used_query_override: bool
    search_id: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PersistedTmdbResolution:
    """One append-only scoring run and its resolution outcome."""

    resolution_id: str
    lookup_id: str
    scoring_version: str
    resolved_at: datetime
    resolution: Resolution


class TmdbCandidateRepository:
    """Persist raw TMDB responses and parsed candidates without selecting a match."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path

    def initialize(self) -> None:
        with duckdb.connect(str(self.path)) as connection:
            connection.execute(
                """
                create table if not exists tmdb_searches (
                    search_id varchar primary key,
                    normalized_title varchar not null,
                    search_query varchar not null,
                    language varchar not null,
                    retrieved_at timestamptz not null,
                    response_json json not null
                )
                """
            )
            columns = {
                row[1]
                for row in connection.execute("pragma table_info('tmdb_searches')").fetchall()
            }
            if "search_query" not in columns:
                connection.execute("alter table tmdb_searches add column search_query varchar")
                connection.execute(
                    "update tmdb_searches set search_query = normalized_title "
                    "where search_query is null"
                )
            connection.execute(
                """
                create table if not exists tmdb_lookup_contexts (
                    lookup_id varchar primary key,
                    source_title varchar not null,
                    normalized_source_title varchar not null,
                    production_year integer,
                    query_titles_json json not null,
                    used_query_override boolean not null,
                    search_id varchar not null,
                    created_at timestamptz not null,
                    foreign key (search_id) references tmdb_searches(search_id),
                    check (production_year is null or production_year between 1900 and 2099)
                )
                """
            )
            connection.execute(
                """
                create table if not exists tmdb_candidates (
                    search_id varchar not null,
                    candidate_rank integer not null,
                    tmdb_id integer not null,
                    media_type varchar not null,
                    title varchar not null,
                    original_title varchar not null,
                    original_language varchar,
                    release_date date,
                    overview varchar,
                    popularity double,
                    vote_average double,
                    vote_count integer,
                    primary key (search_id, candidate_rank),
                    foreign key (search_id) references tmdb_searches(search_id),
                    check (media_type in ('movie', 'tv'))
                )
                """
            )
            connection.execute(
                """
                create table if not exists tmdb_resolutions (
                    resolution_id varchar primary key,
                    lookup_id varchar not null,
                    scoring_version varchar not null,
                    status varchar not null,
                    reason varchar not null,
                    winning_candidate_rank integer,
                    tmdb_id integer,
                    media_type varchar,
                    winning_score double,
                    runner_up_score double,
                    score_margin double,
                    resolved_at timestamptz not null,
                    foreign key (lookup_id) references tmdb_lookup_contexts(lookup_id),
                    check (status in ('matched', 'unresolved'))
                )
                """
            )
            connection.execute(
                """
                create table if not exists tmdb_candidate_scores (
                    resolution_id varchar not null,
                    candidate_rank integer not null,
                    tmdb_id integer not null,
                    title_score double not null,
                    year_score double,
                    total_score double not null,
                    score_rank integer not null,
                    primary key (resolution_id, candidate_rank),
                    foreign key (resolution_id) references tmdb_resolutions(resolution_id)
                )
                """
            )

    def latest(self, normalized_title: str, language: str) -> CachedTmdbSearch | None:
        """Return the latest cached result for an exact normalized query."""
        self.initialize()
        with duckdb.connect(str(self.path), read_only=True) as connection:
            search = connection.execute(
                """
                select search_id, normalized_title, search_query, language, retrieved_at
                from tmdb_searches
                where normalized_title = ? and language = ?
                order by retrieved_at desc, search_id desc
                limit 1
                """,
                [normalized_title, language],
            ).fetchone()
            if search is None:
                return None
            rows = connection.execute(
                """
                select
                    candidate_rank, tmdb_id, media_type, title, original_title,
                    original_language, release_date, overview, popularity,
                    vote_average, vote_count
                from tmdb_candidates
                where search_id = ?
                order by candidate_rank
                """,
                [search[0]],
            ).fetchall()
        return CachedTmdbSearch(
            search_id=search[0],
            normalized_title=search[1],
            search_query=search[2],
            language=search[3],
            retrieved_at=search[4],
            candidates=tuple(TmdbCandidate(*row) for row in rows),
        )

    def save(
        self,
        normalized_title: str,
        search_query: str,
        language: str,
        response: TmdbSearchResponse,
        retrieved_at: datetime | None = None,
    ) -> CachedTmdbSearch:
        """Atomically append one raw response and its parsed candidate rows."""
        if retrieved_at is not None and retrieved_at.tzinfo is None:
            raise ValueError("TMDB retrieval timestamp must be timezone-aware")
        self.initialize()
        search_id = str(uuid4())
        retrieved_at = retrieved_at or datetime.now(UTC)
        with duckdb.connect(str(self.path)) as connection:
            connection.begin()
            try:
                connection.execute(
                    """
                    insert into tmdb_searches (
                        search_id, normalized_title, search_query, language,
                        retrieved_at, response_json
                    ) values (?, ?, ?, ?, ?, ?)
                    """,
                    [
                        search_id,
                        normalized_title,
                        search_query,
                        language,
                        retrieved_at,
                        json.dumps(response.payload, ensure_ascii=False),
                    ],
                )
                if response.candidates:
                    connection.executemany(
                        """
                        insert into tmdb_candidates
                        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        [(search_id, *astuple(candidate)) for candidate in response.candidates],
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return CachedTmdbSearch(
            search_id=search_id,
            normalized_title=normalized_title,
            search_query=search_query,
            language=language,
            retrieved_at=retrieved_at,
            candidates=response.candidates,
        )

    def record_lookup(
        self,
        evidence: TitleEvidence,
        search_id: str,
        *,
        used_query_override: bool,
        created_at: datetime | None = None,
    ) -> TmdbLookupContext:
        """Append the source evidence associated with one selected cached search."""
        self.initialize()
        lookup_id = str(uuid4())
        created_at = created_at or datetime.now(UTC)
        if created_at.tzinfo is None:
            raise ValueError("TMDB lookup timestamp must be timezone-aware")
        normalized_source_title = normalize_title(evidence.source_title).normalized_title
        context = TmdbLookupContext(
            lookup_id=lookup_id,
            source_title=evidence.source_title,
            normalized_source_title=normalized_source_title,
            production_year=evidence.production_year,
            query_titles=evidence.query_titles,
            used_query_override=used_query_override,
            search_id=search_id,
            created_at=created_at,
        )
        with duckdb.connect(str(self.path)) as connection:
            connection.execute(
                "insert into tmdb_lookup_contexts values (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    lookup_id,
                    evidence.source_title,
                    normalized_source_title,
                    evidence.production_year,
                    json.dumps(evidence.query_titles, ensure_ascii=False),
                    used_query_override,
                    search_id,
                    created_at,
                ],
            )
        return context

    def has_resolved_evidence(
        self,
        evidence: TitleEvidence,
        language: str,
        *,
        scoring_version: str = "v1",
    ) -> bool:
        """Return whether equivalent evidence already has this scoring version."""
        self.initialize()
        normalized_source_title = normalize_title(evidence.source_title).normalized_title
        query_titles_json = json.dumps(evidence.query_titles, ensure_ascii=False)
        with duckdb.connect(str(self.path), read_only=True) as connection:
            row = connection.execute(
                """
                select 1
                from tmdb_lookup_contexts as contexts
                inner join tmdb_searches as searches using (search_id)
                inner join tmdb_resolutions as resolutions using (lookup_id)
                where contexts.normalized_source_title = ?
                  and contexts.production_year is not distinct from ?
                  and cast(contexts.query_titles_json as varchar) = ?
                  and searches.language = ?
                  and resolutions.scoring_version = ?
                limit 1
                """,
                [
                    normalized_source_title,
                    evidence.production_year,
                    query_titles_json,
                    language,
                    scoring_version,
                ],
            ).fetchone()
        return row is not None

    def resolve_lookup(
        self,
        lookup_id: str,
        *,
        scoring_version: str = "v1",
        resolved_at: datetime | None = None,
    ) -> PersistedTmdbResolution:
        """Score one lookup and append its component scores and conservative outcome."""
        self.initialize()
        with duckdb.connect(str(self.path), read_only=True) as connection:
            lookup = connection.execute(
                """
                select contexts.production_year, searches.search_query
                from tmdb_lookup_contexts as contexts
                inner join tmdb_searches as searches using (search_id)
                where contexts.lookup_id = ?
                """,
                [lookup_id],
            ).fetchone()
            if lookup is None:
                raise KeyError(f"TMDB lookup {lookup_id!r} was not found")
            rows = connection.execute(
                """
                select
                    candidates.candidate_rank, candidates.tmdb_id,
                    candidates.media_type, candidates.title,
                    candidates.original_title, candidates.original_language,
                    candidates.release_date, candidates.overview,
                    candidates.popularity, candidates.vote_average,
                    candidates.vote_count
                from tmdb_lookup_contexts as contexts
                inner join tmdb_candidates as candidates using (search_id)
                where contexts.lookup_id = ?
                order by candidates.candidate_rank
                """,
                [lookup_id],
            ).fetchall()

        resolution = resolve_candidates(
            lookup[1],
            lookup[0],
            tuple(TmdbCandidate(*row) for row in rows),
        )
        resolution_id = str(uuid4())
        resolved_at = resolution_timestamp(resolved_at)
        winner = resolution.winner
        is_matched = resolution.status is ResolutionStatus.MATCHED
        with duckdb.connect(str(self.path)) as connection:
            connection.begin()
            try:
                connection.execute(
                    """
                    insert into tmdb_resolutions values (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    [
                        resolution_id,
                        lookup_id,
                        scoring_version,
                        resolution.status.value,
                        resolution.reason.value,
                        winner.candidate.rank if winner else None,
                        winner.candidate.tmdb_id if winner and is_matched else None,
                        winner.candidate.media_type if winner and is_matched else None,
                        winner.total_score if winner else None,
                        resolution.runner_up_score,
                        resolution.score_margin,
                        resolved_at,
                    ],
                )
                if resolution.scores:
                    connection.executemany(
                        """
                        insert into tmdb_candidate_scores
                        values (?, ?, ?, ?, ?, ?, ?)
                        """,
                        [
                            (
                                resolution_id,
                                score.candidate.rank,
                                score.candidate.tmdb_id,
                                score.title_score,
                                score.year_score,
                                score.total_score,
                                score.score_rank,
                            )
                            for score in resolution.scores
                        ],
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return PersistedTmdbResolution(
            resolution_id,
            lookup_id,
            scoring_version,
            resolved_at,
            resolution,
        )
