"""Append-only DuckDB cache for confidently matched TMDB entity details."""

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

import duckdb

from greek_tv.enrichment.tmdb import TmdbEntityDetails


@dataclass(frozen=True, slots=True)
class CachedTmdbEntity:
    """One immutable retrieval of stable TMDB entity metadata."""

    entity_detail_id: str
    retrieved_at: datetime
    details: TmdbEntityDetails


@dataclass(frozen=True, slots=True)
class TmdbMetricObservation:
    """One historical observation of mutable TMDB entity metrics."""

    metric_observation_id: str
    entity_detail_id: str
    tmdb_id: int
    media_type: str
    popularity: float | None
    vote_average: float | None
    vote_count: int | None
    observed_at: datetime


class TmdbEntityRepository:
    """Persist and reuse details for accepted movie and television identities."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path

    def initialize(self) -> None:
        with duckdb.connect(str(self.path)) as connection:
            connection.execute(
                """
                create table if not exists tmdb_entity_details (
                    entity_detail_id varchar primary key,
                    tmdb_id integer not null,
                    media_type varchar not null,
                    language varchar not null,
                    title varchar not null,
                    original_title varchar not null,
                    original_language varchar,
                    release_date date,
                    overview varchar,
                    tagline varchar,
                    runtime_minutes integer,
                    status varchar,
                    homepage varchar,
                    imdb_id varchar,
                    genres_json json not null,
                    production_countries_json json not null,
                    production_companies_json json not null,
                    spoken_languages_json json not null,
                    retrieved_at timestamptz not null,
                    response_json json not null,
                    poster_path varchar,
                    check (media_type in ('movie', 'tv')),
                    check (runtime_minutes is null or runtime_minutes >= 0)
                )
                """
            )
            connection.execute(
                "alter table tmdb_entity_details add column if not exists poster_path varchar"
            )
            connection.execute(
                """
                update tmdb_entity_details
                set poster_path = nullif(json_extract_string(response_json, '$.poster_path'), '')
                where poster_path is null
                """
            )
            connection.execute(
                """
                create table if not exists tmdb_entity_metric_observations (
                    metric_observation_id varchar primary key,
                    entity_detail_id varchar not null,
                    tmdb_id integer not null,
                    media_type varchar not null,
                    popularity double,
                    vote_average double,
                    vote_count integer,
                    observed_at timestamptz not null,
                    foreign key (entity_detail_id)
                        references tmdb_entity_details(entity_detail_id),
                    check (media_type in ('movie', 'tv')),
                    check (vote_average is null or vote_average between 0 and 10),
                    check (vote_count is null or vote_count >= 0)
                )
                """
            )
            connection.execute(
                """
                insert into tmdb_entity_metric_observations
                select
                    md5(details.entity_detail_id || ':metrics'),
                    details.entity_detail_id,
                    details.tmdb_id,
                    details.media_type,
                    try_cast(json_extract(details.response_json, '$.popularity') as double),
                    try_cast(json_extract(details.response_json, '$.vote_average') as double),
                    try_cast(json_extract(details.response_json, '$.vote_count') as integer),
                    details.retrieved_at
                from tmdb_entity_details as details
                where not exists (
                    select 1
                    from tmdb_entity_metric_observations as observations
                    where observations.entity_detail_id = details.entity_detail_id
                )
                """
            )

    def latest(self, media_type: str, tmdb_id: int, language: str) -> CachedTmdbEntity | None:
        """Return the newest exact-identity and language cache entry."""
        self.initialize()
        with duckdb.connect(str(self.path), read_only=True) as connection:
            row = connection.execute(
                """
                select
                    entity_detail_id, tmdb_id, media_type, language, title,
                    original_title, original_language, release_date, overview,
                    tagline, runtime_minutes, status, homepage, imdb_id,
                    genres_json, production_countries_json,
                    production_companies_json, spoken_languages_json,
                    retrieved_at, response_json, poster_path
                from tmdb_entity_details
                where media_type = ? and tmdb_id = ? and language = ?
                order by retrieved_at desc, entity_detail_id desc
                limit 1
                """,
                [media_type, tmdb_id, language],
            ).fetchone()
        if row is None:
            return None
        details = TmdbEntityDetails(
            tmdb_id=row[1],
            media_type=row[2],
            language=row[3],
            title=row[4],
            original_title=row[5],
            original_language=row[6],
            release_date=row[7],
            overview=row[8],
            tagline=row[9],
            runtime_minutes=row[10],
            status=row[11],
            homepage=row[12],
            imdb_id=row[13],
            poster_path=row[20],
            genres=tuple(json.loads(row[14])),
            production_countries=tuple(json.loads(row[15])),
            production_companies=tuple(json.loads(row[16])),
            spoken_languages=tuple(json.loads(row[17])),
            popularity=_optional_float_from_payload(row[19], "popularity"),
            vote_average=_optional_float_from_payload(row[19], "vote_average"),
            vote_count=_optional_int_from_payload(row[19], "vote_count"),
            payload=json.loads(row[19]),
        )
        return CachedTmdbEntity(row[0], row[18], details)

    def save(
        self,
        details: TmdbEntityDetails,
        retrieved_at: datetime | None = None,
    ) -> CachedTmdbEntity:
        """Append one complete entity response and its stable parsed attributes."""
        retrieved_at = retrieved_at or datetime.now(UTC)
        if retrieved_at.tzinfo is None:
            raise ValueError("TMDB entity retrieval timestamp must be timezone-aware")
        self.initialize()
        entity_detail_id = str(uuid4())
        metric_observation_id = str(uuid4())
        with duckdb.connect(str(self.path)) as connection:
            connection.begin()
            try:
                connection.execute(
                    """
                    insert into tmdb_entity_details (
                        entity_detail_id, tmdb_id, media_type, language, title,
                        original_title, original_language, release_date, overview,
                        tagline, runtime_minutes, status, homepage, imdb_id,
                        genres_json, production_countries_json,
                        production_companies_json, spoken_languages_json,
                        retrieved_at, response_json, poster_path
                    ) values (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    [
                        entity_detail_id,
                        details.tmdb_id,
                        details.media_type,
                        details.language,
                        details.title,
                        details.original_title,
                        details.original_language,
                        details.release_date,
                        details.overview,
                        details.tagline,
                        details.runtime_minutes,
                        details.status,
                        details.homepage,
                        details.imdb_id,
                        json.dumps(details.genres, ensure_ascii=False),
                        json.dumps(details.production_countries, ensure_ascii=False),
                        json.dumps(details.production_companies, ensure_ascii=False),
                        json.dumps(details.spoken_languages, ensure_ascii=False),
                        retrieved_at,
                        json.dumps(details.payload, ensure_ascii=False),
                        details.poster_path,
                    ],
                )
                connection.execute(
                    """
                    insert into tmdb_entity_metric_observations
                    values (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        metric_observation_id,
                        entity_detail_id,
                        details.tmdb_id,
                        details.media_type,
                        details.popularity,
                        details.vote_average,
                        details.vote_count,
                        retrieved_at,
                    ],
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return CachedTmdbEntity(entity_detail_id, retrieved_at, details)

    def latest_metric(self, media_type: str, tmdb_id: int) -> TmdbMetricObservation | None:
        """Return the newest mutable-metric observation for one entity."""
        self.initialize()
        with duckdb.connect(str(self.path), read_only=True) as connection:
            row = connection.execute(
                """
                select
                    metric_observation_id, entity_detail_id, tmdb_id, media_type,
                    popularity, vote_average, vote_count, observed_at
                from tmdb_entity_metric_observations
                where media_type = ? and tmdb_id = ?
                order by observed_at desc, metric_observation_id desc
                limit 1
                """,
                [media_type, tmdb_id],
            ).fetchone()
        return TmdbMetricObservation(*row) if row else None

    def detailed_identities(self) -> list[tuple[str, int]]:
        """Return distinct identities that have passed matched-detail retrieval."""
        self.initialize()
        with duckdb.connect(str(self.path), read_only=True) as connection:
            return connection.execute(
                """
                select distinct media_type, tmdb_id
                from tmdb_entity_details
                order by media_type, tmdb_id
                """
            ).fetchall()

    def matched_identities(self, schedule_date: date | None = None) -> list[tuple[str, int]]:
        """Return accepted identities, optionally limited by exact broadcast lineage."""
        self.initialize()
        if schedule_date is None:
            query = """
                select distinct media_type, tmdb_id
                from tmdb_resolutions
                where status = 'matched'
                  and media_type is not null
                  and tmdb_id is not null
                order by media_type, tmdb_id
            """
            parameters = []
        else:
            query = """
                select distinct
                    resolutions.media_type,
                    resolutions.tmdb_id
                from tmdb_resolutions as resolutions
                inner join broadcast_enrichment_lookups as lineage
                    on resolutions.lookup_id = lineage.lookup_id
                inner join broadcast_observations as observations
                    on lineage.observation_id = observations.observation_id
                inner join ingestion_runs as runs
                    on observations.run_id = runs.run_id
                where resolutions.status = 'matched'
                  and resolutions.media_type is not null
                  and resolutions.tmdb_id is not null
                  and runs.schedule_date = ?
                order by resolutions.media_type, resolutions.tmdb_id
            """
            parameters = [schedule_date]
        with duckdb.connect(str(self.path), read_only=True) as connection:
            rows = connection.execute(query, parameters).fetchall()
        return rows


def _optional_float_from_payload(payload: str, key: str) -> float | None:
    value = json.loads(payload).get(key)
    return float(value) if isinstance(value, int | float) else None


def _optional_int_from_payload(payload: str, key: str) -> int | None:
    value = json.loads(payload).get(key)
    return value if isinstance(value, int) else None
