from datetime import date, datetime

import duckdb
import pytest

from greek_tv.dashboard import (
    DashboardDataError,
    available_channels,
    available_dates,
    available_sources,
    daily_highlights,
    dates_in_horizon,
    imdb_url,
    poster_url,
)


def create_highlights_mart(path) -> None:
    with duckdb.connect(str(path)) as connection:
        connection.execute("create schema greek_tv_marts")
        connection.execute(
            """
            create table greek_tv_marts.dim_channels (
                source varchar,
                channel varchar
            )
            """
        )
        connection.executemany(
            "insert into greek_tv_marts.dim_channels values (?, ?)",
            [("programmatileorasis", "alpha"), ("programmatileorasis", "star")],
        )
        connection.execute(
            """
            create table greek_tv_marts.mart_daily_highlights (
                source varchar,
                channel varchar,
                schedule_date date,
                highlight_rank integer,
                overall_highlight_rank integer,
                starts_at_local timestamp,
                schedule_title varchar,
                programme_title varchar,
                original_title varchar,
                release_year integer,
                runtime_minutes integer,
                genres_json json,
                media_type varchar,
                tmdb_id integer,
                match_confidence double,
                metadata_retrieved_at timestamp,
                imdb_id varchar,
                poster_path varchar,
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
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?
            )
            """,
            [
                (
                    "programmatileorasis",
                    "alpha",
                    date(2026, 8, 1),
                    1,
                    1,
                    datetime(2026, 8, 1, 21),
                    "Top across channels",
                    "Top across channels",
                    "Top across channels",
                    2021,
                    138,
                    '["Drama"]',
                    "movie",
                    456,
                    96.0,
                    datetime(2026, 8, 2, 9),
                    "tt456",
                    "/top.jpg",
                    9.0,
                    2000,
                    30.0,
                    90.0,
                    70.0,
                    40.0,
                    81.0,
                    datetime(2026, 8, 2, 10),
                    "v1",
                    "explanation",
                ),
                (
                    "programmatileorasis",
                    "star",
                    date(2026, 8, 1),
                    1,
                    2,
                    datetime(2026, 8, 1, 22),
                    "Ελληνικός τίτλος",
                    "Local title",
                    "Original title",
                    2020,
                    90,
                    '["Comedy"]',
                    "movie",
                    123,
                    93.0,
                    datetime(2026, 8, 2, 9),
                    "tt123",
                    "/poster.jpg",
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
                    1,
                    datetime(2026, 7, 31, 21),
                    "Another title",
                    "Another title",
                    None,
                    None,
                    None,
                    "[]",
                    "movie",
                    789,
                    88.0,
                    datetime(2026, 8, 1, 9),
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
    assert available_channels(database, "programmatileorasis") == ["alpha", "star"]
    assert available_dates(database, "programmatileorasis", None) == [
        date(2026, 8, 1),
        date(2026, 7, 31),
    ]
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
    assert rows[0]["channel"] == "star"
    assert rows[0]["channel_highlight_rank"] == 1
    assert rows[0]["overall_highlight_rank"] == 2
    assert poster_url(rows[0]["poster_path"]) == "https://image.tmdb.org/t/p/w500/poster.jpg"


def test_dashboard_ranks_highlights_across_all_channels(tmp_path) -> None:
    database = tmp_path / "dashboard.duckdb"
    create_highlights_mart(database)

    rows = daily_highlights(
        database,
        "programmatileorasis",
        None,
        date(2026, 8, 1),
        limit=2,
    )

    assert [(row["highlight_rank"], row["channel"]) for row in rows] == [
        (1, "alpha"),
        (2, "star"),
    ]
    assert rows[0]["schedule_title"] == "Top across channels"


def test_dashboard_filters_a_dynamic_channel_selection(tmp_path) -> None:
    database = tmp_path / "dashboard.duckdb"
    create_highlights_mart(database)

    rows = daily_highlights(
        database,
        "programmatileorasis",
        ["star"],
        date(2026, 8, 1),
        limit=4,
    )

    assert [(row["channel"], row["overall_highlight_rank"]) for row in rows] == [("star", 2)]


def test_poster_url_handles_missing_path() -> None:
    assert poster_url(None) is None


def test_imdb_url_accepts_only_title_identifiers() -> None:
    assert imdb_url("tt1234567") == "https://www.imdb.com/title/tt1234567/"
    assert imdb_url(None) is None
    assert imdb_url("nm1234567") is None
    assert imdb_url('tt123" onclick="alert(1)') is None


def test_dates_in_horizon_includes_today_and_requested_number_of_days() -> None:
    available = [date(2026, 8, 12), date(2026, 8, 11), date(2026, 8, 10), date(2026, 8, 9)]

    assert dates_in_horizon(available, date(2026, 8, 9), 3) == [
        date(2026, 8, 11),
        date(2026, 8, 10),
        date(2026, 8, 9),
    ]
    with pytest.raises(ValueError, match="at least 1"):
        dates_in_horizon(available, date(2026, 8, 9), 0)


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
