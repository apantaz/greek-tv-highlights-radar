"""DuckDB cache for reproducible TMDB candidate searches."""

import json
from dataclasses import astuple, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import duckdb

from greek_tv.enrichment.evidence import TitleEvidence
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
