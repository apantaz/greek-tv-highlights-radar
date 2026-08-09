"""Read-only query boundary for the Streamlit analytics application."""

import re
from datetime import date
from pathlib import Path
from typing import Any

import duckdb

# Use schema-qualified access so an overridden DuckDB filename does not change the
# catalog name expected by the application.
HIGHLIGHTS_RELATION = "greek_tv_marts.mart_daily_highlights"
CHANNELS_RELATION = "greek_tv_marts.dim_channels"
TMDB_POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"
TMDB_TITLE_URL = "https://www.themoviedb.org"
TMDB_DISPLAY_LANGUAGE = "el-GR"
IMDB_TITLE_URL = "https://www.imdb.com/title"
IMDB_ID_PATTERN = re.compile(r"^tt\d+$")


class DashboardDataError(RuntimeError):
    """Raised when the analytics database cannot serve the dashboard."""


def _query(
    database_path: Path,
    sql: str,
    parameters: list[object] | None = None,
) -> list[dict[str, Any]]:
    """Execute a read-only query and return rows keyed by column name."""
    path = database_path.expanduser().resolve()
    if not path.is_file():
        raise DashboardDataError(f"DuckDB database does not exist: {path}")

    try:
        with duckdb.connect(str(path), read_only=True) as connection:
            result = connection.execute(sql, parameters or [])
            columns = [column[0] for column in result.description]
            return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]
    except duckdb.Error as error:
        raise DashboardDataError(
            "Could not read the daily-highlights mart. Run "
            "`cd dbt && dbt build --select +mart_daily_highlights` and ensure no "
            "other process holds an incompatible DuckDB lock."
        ) from error


def available_sources(database_path: Path) -> list[str]:
    """Return sources represented in the highlights archive."""
    rows = _query(
        database_path,
        f"""
        select distinct source
        from {HIGHLIGHTS_RELATION}
        order by source
        """,
    )
    return [row["source"] for row in rows]


def available_channels(database_path: Path, source: str) -> list[str]:
    """Return dynamically discovered channels for one source."""
    rows = _query(
        database_path,
        f"""
        select distinct channel
        from {CHANNELS_RELATION}
        where source = ?
        order by channel
        """,
        [source],
    )
    return [row["channel"] for row in rows]


def available_dates(database_path: Path, source: str, channel: str | None) -> list[date]:
    """Return archived dates for one channel or all channels."""
    rows = _query(
        database_path,
        f"""
        select distinct schedule_date
        from {HIGHLIGHTS_RELATION}
        where source = ?
          and (? is null or channel = ?)
        order by schedule_date desc
        """,
        [source, channel, channel],
    )
    return [row["schedule_date"] for row in rows]


def daily_highlights(
    database_path: Path,
    source: str,
    channel: str | list[str] | None,
    schedule_date: date,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return top broadcasts across all channels or within one channel-day."""
    if limit < 1:
        raise ValueError("limit must be at least 1")

    channels = [channel] if isinstance(channel, str) else channel
    channel_filter = ""
    filter_parameters: list[object] = []
    if channels:
        placeholders = ", ".join("?" for _ in channels)
        channel_filter = f"and channel in ({placeholders})"
        filter_parameters.extend(channels)
    use_channel_rank = isinstance(channel, str)

    return _query(
        database_path,
        f"""
        select
            case
                when not ? then overall_highlight_rank
                else highlight_rank
            end as highlight_rank,
            highlight_rank as channel_highlight_rank,
            overall_highlight_rank,
            channel,
            schedule_date,
            starts_at_local,
            schedule_title,
            programme_title,
            original_title,
            release_year,
            runtime_minutes,
            genres_json,
            media_type,
            tmdb_id,
            match_confidence,
            metadata_retrieved_at,
            imdb_id,
            poster_path,
            vote_average,
            vote_count,
            popularity,
            quality_score,
            confidence_score,
            popularity_score,
            highlight_score,
            metrics_observed_at,
            ranking_version,
            ranking_explanation
        from {HIGHLIGHTS_RELATION}
        where source = ?
          and schedule_date = ?
          {channel_filter}
        order by highlight_rank
        limit ?
        """,
        [use_channel_rank, source, schedule_date, *filter_parameters, limit],
    )


def poster_url(poster_path: str | None) -> str | None:
    """Build the documented TMDB w500 asset URL for a poster path."""
    if not poster_path:
        return None
    return f"{TMDB_POSTER_BASE_URL}/{poster_path.lstrip('/')}"


def tmdb_url(media_type: str | None, tmdb_id: int | None) -> str | None:
    """Return a safe TMDB title URL for a supported positive identity."""
    if media_type not in {"movie", "tv"}:
        return None
    if not isinstance(tmdb_id, int) or isinstance(tmdb_id, bool) or tmdb_id < 1:
        return None
    return f"{TMDB_TITLE_URL}/{media_type}/{tmdb_id}?language={TMDB_DISPLAY_LANGUAGE}"


def imdb_url(imdb_id: str | None) -> str | None:
    """Return a safe IMDb title URL only for a valid title identifier."""
    if not imdb_id or not IMDB_ID_PATTERN.fullmatch(imdb_id):
        return None
    return f"{IMDB_TITLE_URL}/{imdb_id}/"


def dates_in_horizon(
    available: list[date],
    start_date: date,
    number_of_days: int,
) -> list[date]:
    """Return available dates within an inclusive forward-looking horizon."""
    if number_of_days < 1:
        raise ValueError("number_of_days must be at least 1")
    end_date = date.fromordinal(start_date.toordinal() + number_of_days - 1)
    return [value for value in available if start_date <= value <= end_date]
