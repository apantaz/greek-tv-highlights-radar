"""Append-only DuckDB cache for confidently matched TMDB entity details."""

import json
from dataclasses import dataclass
from datetime import UTC, datetime
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
                    check (media_type in ('movie', 'tv')),
                    check (runtime_minutes is null or runtime_minutes >= 0)
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
                    retrieved_at, response_json
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
            genres=tuple(json.loads(row[14])),
            production_countries=tuple(json.loads(row[15])),
            production_companies=tuple(json.loads(row[16])),
            spoken_languages=tuple(json.loads(row[17])),
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
        with duckdb.connect(str(self.path)) as connection:
            connection.execute(
                """
                insert into tmdb_entity_details values (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
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
                ],
            )
        return CachedTmdbEntity(entity_detail_id, retrieved_at, details)

    def matched_identities(self) -> list[tuple[str, int]]:
        """Return distinct identities accepted by any resolution run."""
        self.initialize()
        with duckdb.connect(str(self.path), read_only=True) as connection:
            rows = connection.execute(
                """
                select distinct media_type, tmdb_id
                from tmdb_resolutions
                where status = 'matched'
                  and media_type is not null
                  and tmdb_id is not null
                order by media_type, tmdb_id
                """
            ).fetchall()
        return rows
