"""Interactive daily-highlights dashboard backed by tested dbt marts."""

from datetime import date
from pathlib import Path

import streamlit as st
from greek_tv.config import DEFAULT_DATABASE_PATH
from greek_tv.dashboard import (
    DashboardDataError,
    available_channels,
    available_dates,
    available_sources,
    daily_highlights,
)

st.set_page_config(page_title="Greek TV Highlights Radar", page_icon="📺", layout="wide")


@st.cache_data(ttl=60)
def load_sources(database_path: str, database_modified_at: float) -> list[str]:
    """Load source options, invalidating when the database changes."""
    del database_modified_at
    return available_sources(Path(database_path))


@st.cache_data(ttl=60)
def load_channels(database_path: str, database_modified_at: float, source: str) -> list[str]:
    """Load channel options for a source."""
    del database_modified_at
    return available_channels(Path(database_path), source)


@st.cache_data(ttl=60)
def load_dates(
    database_path: str,
    database_modified_at: float,
    source: str,
    channel: str,
) -> list[date]:
    """Load archived dates for a source and channel."""
    del database_modified_at
    return available_dates(Path(database_path), source, channel)


@st.cache_data(ttl=60)
def load_highlights(
    database_path: str,
    database_modified_at: float,
    source: str,
    channel: str,
    schedule_date: date,
    limit: int,
) -> list[dict[str, object]]:
    """Load ranked highlights for the active filters."""
    del database_modified_at
    return daily_highlights(Path(database_path), source, channel, schedule_date, limit)


def stop_with_error(message: str) -> None:
    """Render an actionable error and stop the current Streamlit run."""
    st.error(message)
    st.stop()


st.title("Greek TV Highlights Radar")
st.caption("Explainable daily recommendations from the tested analytics warehouse")

with st.sidebar:
    st.header("Archive filters")
    configured_path = st.text_input(
        "DuckDB database",
        value=str(DEFAULT_DATABASE_PATH),
        help="Use the same database that dbt builds.",
    )
    result_limit = st.slider("Highlights to show", min_value=1, max_value=20, value=10)
    if st.button("Refresh data", use_container_width=True):
        st.cache_data.clear()

database_path = Path(configured_path).expanduser().resolve()
if not database_path.is_file():
    stop_with_error(
        f"Database not found at `{database_path}`. Run ingestion and dbt first, or choose "
        "the correct DuckDB file in the sidebar."
    )

database_modified_at = database_path.stat().st_mtime

try:
    sources = load_sources(str(database_path), database_modified_at)
    if not sources:
        stop_with_error("The daily-highlights mart exists but contains no eligible broadcasts.")
    source = st.sidebar.selectbox("Source", sources)

    channels = load_channels(str(database_path), database_modified_at, source)
    if not channels:
        stop_with_error("No channels with eligible highlights were found for this source.")
    channel = st.sidebar.selectbox("Channel", channels)

    dates = load_dates(str(database_path), database_modified_at, source, channel)
    if not dates:
        stop_with_error("No archived highlight dates were found for this channel.")
    schedule_date = st.sidebar.selectbox("Schedule date", dates)

    highlights = load_highlights(
        str(database_path),
        database_modified_at,
        source,
        channel,
        schedule_date,
        result_limit,
    )
except DashboardDataError as error:
    stop_with_error(str(error))

st.subheader(f"{channel} highlights · {schedule_date:%d %B %Y}")
st.caption(
    "Only broadcasts with a confidently resolved programme and a TMDB metric observation "
    "are eligible."
)

if not highlights:
    st.info("No eligible highlights match the selected channel and date.")
    st.stop()

top_highlight = highlights[0]
metric_columns = st.columns(3)
metric_columns[0].metric("Eligible results shown", len(highlights))
metric_columns[1].metric("Top highlight score", f"{top_highlight['highlight_score']:.2f}")
metric_columns[2].metric("Ranking policy", str(top_highlight["ranking_version"]))

for highlight in highlights:
    start_time = highlight["starts_at_local"].strftime("%H:%M")
    title = highlight["programme_title"] or highlight["schedule_title"]
    with st.container(border=True):
        heading, score = st.columns([4, 1])
        heading.subheader(f"#{highlight['highlight_rank']} · {start_time} · {title}")
        heading.caption(
            f"Schedule title: {highlight['schedule_title']}"
            + (
                f" · Original title: {highlight['original_title']}"
                if highlight["original_title"]
                else ""
            )
        )
        score.metric("Highlight score", f"{highlight['highlight_score']:.2f}")

        components = st.columns(3)
        components[0].metric("Quality · 70%", f"{highlight['quality_score']:.2f}")
        components[1].metric("Vote confidence · 20%", f"{highlight['confidence_score']:.2f}")
        components[2].metric("Popularity · 10%", f"{highlight['popularity_score']:.2f}")

        with st.expander("Ranking evidence"):
            st.write(
                {
                    "TMDB vote average": highlight["vote_average"],
                    "TMDB vote count": highlight["vote_count"],
                    "TMDB popularity": highlight["popularity"],
                    "Metrics observed at": highlight["metrics_observed_at"],
                    "IMDb ID": highlight["imdb_id"],
                    "Policy": highlight["ranking_explanation"],
                }
            )

st.caption(f"Read-only data source: `{database_path}`")
