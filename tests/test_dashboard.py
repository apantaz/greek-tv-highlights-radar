from datetime import date, datetime

import duckdb
import pytest

from greek_tv.dashboard import (
    DashboardDataError,
    available_channels,
    available_dates,
    available_sources,
    daily_highlights,
)


def create_highlights_mart(path) -> None:
    with duckdb.connect(str(path)) as connection:
        connection.execute("create schema greek_tv_marts")
        connection.execute(
            """
            create table greek_tv_marts.mart_daily_highlights (
                source varchar,
                channel varchar,
                schedule_date date,
                highlight_rank integer,
                starts_at_local timestamp,
                schedule_title varchar,
                programme_title varchar,
                original_title varchar,
                release_year integer,
                imdb_id varchar,
                vote_average double,
                vote_count integer,
                popularity double,
                quality_score double,
                confidence_score double,
                popularity_score double,
                highlight_score double,
                metrics_observed_at timestamp,
                ranking_version varchar,
                ranking_explanation varchar
            )
            """
        )
        connection.executemany(
            """
            insert into greek_tv_marts.mart_daily_highlights values (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            [
                (
                    "programmatileorasis",
                    "star",
                    date(2026, 8, 1),
                    1,
                    datetime(2026, 8, 1, 22),
                    "Ελληνικός τίτλος",
                    "Local title",
                    "Original title",
                    2020,
                    "tt123",
                    8.0,
                    1000,
                    20.0,
                    80.0,
                    60.0,
                    30.0,
                    71.0,
                    datetime(2026, 8, 2, 10),
                    "v1",
                    "explanation",
                ),
                (
                    "programmatileorasis",
                    "star",
                    date(2026, 7, 31),
                    1,
                    datetime(2026, 7, 31, 21),
                    "Another title",
                    "Another title",
                    None,
                    None,
                    None,
                    7.0,
                    500,
                    10.0,
                    70.0,
                    50.0,
                    20.0,
                    61.0,
                    datetime(2026, 8, 1, 10),
                    "v1",
                    "explanation",
                ),
            ],
        )


def test_dashboard_filters_and_returns_ranked_highlights(tmp_path) -> None:
    database = tmp_path / "dashboard.duckdb"
    create_highlights_mart(database)

    assert available_sources(database) == ["programmatileorasis"]
    assert available_channels(database, "programmatileorasis") == ["star"]
    assert available_dates(database, "programmatileorasis", "star") == [
        date(2026, 8, 1),
        date(2026, 7, 31),
    ]

    rows = daily_highlights(
        database,
        "programmatileorasis",
        "star",
        date(2026, 8, 1),
        limit=1,
    )

    assert len(rows) == 1
    assert rows[0]["schedule_title"] == "Ελληνικός τίτλος"
    assert rows[0]["highlight_score"] == 71.0
    assert rows[0]["ranking_version"] == "v1"


def test_dashboard_reports_missing_database(tmp_path) -> None:
    with pytest.raises(DashboardDataError, match="does not exist"):
        available_sources(tmp_path / "missing.duckdb")


def test_dashboard_reports_missing_mart(tmp_path) -> None:
    database = tmp_path / "empty.duckdb"
    with duckdb.connect(str(database)):
        pass

    with pytest.raises(DashboardDataError, match="dbt build"):
        available_sources(database)


def test_daily_highlights_rejects_invalid_limit(tmp_path) -> None:
    with pytest.raises(ValueError, match="at least 1"):
        daily_highlights(tmp_path / "unused.duckdb", "source", "channel", date.today(), 0)
