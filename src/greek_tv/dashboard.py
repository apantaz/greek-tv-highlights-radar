"""Read-only query boundary for the Streamlit analytics application."""

from datetime import date
from pathlib import Path
from typing import Any

import duckdb

# Use schema-qualified access so an overridden DuckDB filename does not change the
# catalog name expected by the application.
HIGHLIGHTS_RELATION = "greek_tv_marts.mart_daily_highlights"


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
    """Return channels with eligible highlights for one source."""
    rows = _query(
        database_path,
        f"""
        select distinct channel
        from {HIGHLIGHTS_RELATION}
        where source = ?
        order by channel
        """,
        [source],
    )
    return [row["channel"] for row in rows]


def available_dates(database_path: Path, source: str, channel: str) -> list[date]:
    """Return archived dates in reverse chronological order."""
    rows = _query(
        database_path,
        f"""
        select distinct schedule_date
        from {HIGHLIGHTS_RELATION}
        where source = ? and channel = ?
        order by schedule_date desc
        """,
        [source, channel],
    )
    return [row["schedule_date"] for row in rows]


def daily_highlights(
    database_path: Path,
    source: str,
    channel: str,
    schedule_date: date,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return the highest-ranked eligible broadcasts for one channel-day."""
    if limit < 1:
        raise ValueError("limit must be at least 1")

    return _query(
        database_path,
        f"""
        select
            highlight_rank,
            starts_at_local,
            schedule_title,
            programme_title,
            original_title,
            release_year,
            imdb_id,
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
          and channel = ?
          and schedule_date = ?
        order by highlight_rank
        limit ?
        """,
        [source, channel, schedule_date, limit],
    )
