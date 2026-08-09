"""Interactive daily-highlights dashboard backed by tested dbt marts."""

import json
from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

import httpx

import streamlit as st
from greek_tv.config import DEFAULT_DATABASE_PATH
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
from greek_tv.scraper.channels import ChannelCatalogError
from greek_tv.scraper.client import ScheduleClient

st.set_page_config(page_title="Greek TV Highlights Radar", page_icon="📺", layout="wide")

POSTER_PLACEHOLDER = Path(__file__).parent / "assets" / "poster-placeholder.svg"
ATHENS_TIMEZONE = ZoneInfo("Europe/Athens")
VIEWING_HORIZONS = {
    "Tonight": 1,
    "Tomorrow": 1,
    "Next 3 days": 3,
}
ARCHIVE_VIEW = "Custom date"
CHANNEL_PRIORITY = {
    "STAR": 0,
    "ANT1": 1,
    "MEGA": 2,
    "ALPHA": 3,
    "ΣΚΑΪ": 4,
    "Open Beyond": 5,
    "ΕΡΤ1": 6,
    "ΕΡΤ2": 7,
    "ΕΡΤ3": 8,
}
POSTER_PLACEHOLDER_URI = "data:image/svg+xml," + quote(
    POSTER_PLACEHOLDER.read_text(encoding="utf-8")
)

st.html(
    """
    <style>
    :root {
        --app-bg: #07111f;
        --card-bg: #101d2e;
        --card-border: rgba(148, 163, 184, 0.16);
        --muted: #94a3b8;
        --text: #f8fafc;
        --accent: #35d0ba;
        --accent-soft: rgba(53, 208, 186, 0.12);
        --gold: #f5c518;
    }
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 80% -10%, rgba(34, 211, 238, 0.11), transparent 35rem),
            var(--app-bg);
        color: var(--text);
    }
    [data-testid="stHeader"], [data-testid="stFooter"] {
        background: transparent;
    }
    [data-testid="stSidebar"] {
        background: #0b1727;
        border-right: 1px solid var(--card-border);
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: var(--muted);
    }
    .block-container {
        max-width: 1440px;
        padding-bottom: 3rem;
        padding-top: 2.5rem;
    }
    .app-hero {
        border-bottom: 1px solid var(--card-border);
        margin-bottom: 1.75rem;
        padding: 1.5rem 0 2rem;
    }
    .brand-mark {
        align-items: center;
        color: var(--accent);
        display: flex;
        font-size: 0.78rem;
        font-weight: 800;
        gap: 0.55rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
    }
    .brand-dot {
        background: var(--accent);
        border-radius: 50%;
        box-shadow: 0 0 1rem rgba(53, 208, 186, 0.7);
        height: 0.55rem;
        width: 0.55rem;
    }
    .app-hero h1 {
        color: var(--text);
        font-size: clamp(2.25rem, 5vw, 4.6rem);
        letter-spacing: -0.055em;
        line-height: 0.98;
        margin: 1rem 0;
        max-width: 900px;
    }
    .app-hero p {
        color: var(--muted);
        font-size: 1.05rem;
        line-height: 1.65;
        margin: 0;
        max-width: 720px;
    }
    .sidebar-brand {
        color: var(--text);
        font-size: 1.15rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        padding: 0.5rem 0 1.2rem;
    }
    .sidebar-label {
        color: var(--accent);
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.14em;
        margin-bottom: 0.25rem;
        text-transform: uppercase;
    }
    .section-heading {
        align-items: end;
        display: flex;
        justify-content: space-between;
        margin: 0.5rem 0 1rem;
    }
    .section-heading h2 {
        color: var(--text);
        font-size: 1.8rem;
        letter-spacing: -0.035em;
        margin: 0;
    }
    .section-heading p {
        color: var(--muted);
        margin: 0.35rem 0 0;
    }
    .summary-strip {
        display: flex;
        flex-wrap: wrap;
        gap: 0.65rem;
        margin-bottom: 1.5rem;
    }
    .summary-chip {
        background: rgba(148, 163, 184, 0.08);
        border: 1px solid var(--card-border);
        border-radius: 999px;
        color: var(--muted);
        font-size: 0.82rem;
        padding: 0.45rem 0.75rem;
    }
    .summary-chip strong {
        color: var(--text);
        font-weight: 700;
    }
    .programme-card {
        background: linear-gradient(180deg, rgba(16, 29, 46, 0.98), rgba(11, 23, 39, 0.98));
        border: 1px solid var(--card-border);
        border-radius: 0.9rem;
        box-shadow: 0 1rem 2.5rem rgba(0, 0, 0, 0.16);
        color: inherit;
        display: block;
        height: 100%;
        overflow: hidden;
        padding: 0.65rem;
        text-decoration: none !important;
        transition: border-color 160ms ease, transform 160ms ease;
    }
    .programme-card:hover {
        border-color: rgba(53, 208, 186, 0.42);
        box-shadow: 0 1.25rem 3rem rgba(0, 0, 0, 0.28);
        transform: translateY(-4px);
    }
    .programme-card:hover .poster-frame img {
        transform: scale(1.035);
    }
    .programme-card.unavailable {
        cursor: default;
    }
    .programme-card.unavailable:hover {
        border-color: var(--card-border);
        transform: none;
    }
    .poster-frame {
        aspect-ratio: 2 / 3;
        background: #17212b;
        border-radius: 0.6rem;
        overflow: hidden;
        position: relative;
        width: 100%;
    }
    .poster-frame img {
        display: block;
        height: 100%;
        object-fit: cover;
        pointer-events: none;
        user-select: none;
        width: 100%;
        transition: transform 220ms ease;
    }
    .rank-badge, .channel-badge {
        backdrop-filter: blur(8px);
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 800;
        position: absolute;
        top: 0.65rem;
        z-index: 1;
    }
    .rank-badge {
        background: var(--accent);
        color: #042f2e;
        left: 0.65rem;
        padding: 0.32rem 0.55rem;
    }
    .channel-badge {
        background: rgba(7, 17, 31, 0.78);
        color: var(--text);
        max-width: 55%;
        overflow: hidden;
        padding: 0.32rem 0.6rem;
        right: 0.65rem;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .programme-heading {
        color: var(--text);
        font-size: 1.02rem;
        font-weight: 700;
        line-height: 1.25;
        min-height: 2.6rem;
        margin-top: 0.75rem;
    }
    .programme-details {
        color: var(--muted);
        font-size: 0.8rem;
        min-height: 2.35rem;
    }
    .rating-star {
        color: var(--gold);
        font-size: 1.15rem;
        line-height: 1;
    }
    .rating-value {
        color: var(--text);
        font-size: 1.05rem;
        font-weight: 700;
    }
    .rating-label {
        color: var(--muted);
        font-size: 0.8rem;
    }
    .score-row {
        align-items: center;
        border-top: 1px solid var(--card-border);
        display: flex;
        justify-content: space-between;
        margin-top: 0.7rem;
        padding-top: 0.7rem;
    }
    .highlight-pill {
        background: var(--accent-soft);
        border: 1px solid rgba(53, 208, 186, 0.2);
        border-radius: 999px;
        color: var(--accent);
        font-size: 0.78rem;
        font-weight: 800;
        padding: 0.32rem 0.55rem;
    }
    .evidence-row {
        margin-bottom: 0.7rem;
    }
    .evidence-label {
        color: var(--muted);
        display: flex;
        font-size: 0.75rem;
        justify-content: space-between;
        margin-bottom: 0.25rem;
    }
    .evidence-track {
        background: rgba(148, 163, 184, 0.12);
        border-radius: 999px;
        height: 0.35rem;
        overflow: hidden;
    }
    .evidence-fill {
        background: linear-gradient(90deg, var(--accent), #22d3ee);
        border-radius: inherit;
        height: 100%;
    }
    .evidence-meta {
        color: var(--muted);
        font-size: 0.72rem;
        line-height: 1.55;
        margin-top: 0.8rem;
    }
    .card-cta {
        align-items: center;
        color: var(--accent);
        display: flex;
        font-size: 0.75rem;
        font-weight: 800;
        justify-content: space-between;
        letter-spacing: 0.02em;
        margin-top: 0.8rem;
    }
    .app-footer {
        border-top: 1px solid var(--card-border);
        color: var(--muted);
        font-size: 0.78rem;
        margin-top: 2.5rem;
        padding-top: 1.25rem;
    }
    .empty-state {
        background: linear-gradient(135deg, rgba(53, 208, 186, 0.08), rgba(34, 211, 238, 0.03));
        border: 1px solid rgba(53, 208, 186, 0.2);
        border-radius: 1rem;
        padding: 2.5rem;
        text-align: center;
    }
    .empty-state h3 {
        color: var(--text);
        margin: 0 0 0.6rem;
    }
    .empty-state p {
        color: var(--muted);
        margin: 0 auto;
        max-width: 620px;
    }
    div[data-testid="stExpander"] {
        background: rgba(148, 163, 184, 0.04);
        border-color: var(--card-border);
    }
    .card-grid, .kpi-grid {
        display: grid;
        gap: 1rem;
        grid-template-columns: repeat(4, minmax(0, 1fr));
    }
    .card-grid { margin-bottom: 1.75rem; }
    .kpi-grid { margin: 1.25rem 0 1.5rem; }
    .kpi-card {
        align-items: center;
        background: linear-gradient(145deg, rgba(16,29,46,.98), rgba(11,23,39,.98));
        border: 1px solid var(--card-border); border-radius: .85rem; display: flex;
        gap: .9rem; min-height: 5.25rem; padding: 1rem;
    }
    .kpi-icon { font-size: 1.65rem; }
    .kpi-value { color: var(--text); font-size: 1.45rem; font-weight: 800; line-height: 1; }
    .kpi-label { color: var(--muted); font-size: .77rem; margin-top: .35rem; }
    .programme-meta {
        color: var(--muted); font-size: .74rem; margin-top: .45rem; min-height: 2.15rem;
    }
    .dual-metric { border-top: 1px solid var(--card-border); display: grid; gap: .5rem;
        grid-template-columns: 1fr 1fr; margin-top: .75rem; padding-top: .75rem; }
    .metric-name { color: var(--muted); font-size: .7rem; }
    .metric-number { color: var(--accent); font-size: 1.2rem; font-weight: 800; }
    .why-title { background: rgba(148,163,184,.07); border: 1px solid var(--card-border);
        border-radius: .45rem; color: var(--text); font-size: .75rem; font-weight: 700;
        margin: .75rem 0; padding: .55rem .65rem; }
    .continuation {
        align-items: center; background: rgba(16,29,46,.72);
        border: 1px solid var(--card-border); border-radius: .85rem;
        display: flex; justify-content: space-between; margin-top: .5rem; padding: 1rem 1.2rem;
    }
    .continuation strong { color: var(--text); }
    .continuation span { color: var(--muted); font-size: .8rem; }
    @media (max-width: 1100px) {
        .card-grid, .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 640px) { .card-grid, .kpi-grid { grid-template-columns: 1fr; } }
    @media (max-width: 800px) {
        .app-hero h1 { font-size: 2.5rem; }
        .block-container { padding-top: 1rem; }
    }
    /* Reference UI: fixed navigation rail and dense cinematic content canvas. */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 58% 0%, #071729 0, #020b16 48%, #020914 100%);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #020c18, #020914);
        min-width: 268px;
        width: 268px;
    }
    [data-testid="stSidebarContent"] { padding: 1.65rem 1.5rem 1.25rem; }
    .block-container { max-width: 1540px; padding: 1.7rem 2.4rem 2rem; }
    .sidebar-brand {
        align-items: center; display: flex; font-size: 1.2rem; gap: .8rem;
        line-height: 1.25; padding: 0 0 2.7rem;
    }
    .tv-mark {
        align-items: center; border: 2px solid #20e0cf; border-radius: .25rem;
        color: #20e0cf; display: flex; font-size: 1.45rem; height: 2.2rem;
        justify-content: center; width: 2.7rem;
    }
    .sidebar-label { color: #20e0cf; font-size: .78rem; margin-bottom: .75rem; }
    .all-channel-row {
        background: linear-gradient(90deg, rgba(17,190,180,.18), rgba(17,190,180,.11));
        border: 1px solid rgba(32,224,207,.22); border-radius: .55rem;
        color: #20e0cf; font-size: .86rem; margin-bottom: .45rem; padding: .75rem .9rem;
    }
    .channel-logo-frame {
        align-items: center; display: flex; height: 2.45rem; justify-content: center;
        width: 2.4rem;
    }
    .channel-logo-frame img {
        display: block; height: 1.65rem; max-width: 2.2rem; object-fit: contain; width: 100%;
    }
    .channel-name {
        align-items: center; color: #e5edf7; display: flex; font-size: .82rem;
        height: 2.45rem; white-space: nowrap;
    }
    [data-testid="stSidebar"] [data-testid="stCheckbox"] { margin: 0; }
    [data-testid="stSidebar"] [data-testid="stCheckbox"] label {
        align-items: center; color: #e5edf7; display: flex; justify-content: space-between;
        min-height: 2.45rem; width: 100%;
    }
    [data-testid="stSidebar"] [data-testid="stCheckbox"] label p {
        color: #e5edf7; font-size: .82rem;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button {
        background: transparent; border: 0; color: #c6d1df; font-size: .72rem; padding: .4rem 0;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button:hover { color: #20e0cf; }
    .about-card {
        background: rgba(11,24,39,.75); border: 1px solid #17283b; border-radius: .6rem;
        color: #f5f7fb; font-size: .78rem; line-height: 1.65; margin-top: 1.1rem; padding: 1rem;
    }
    .about-card p { color: #aeb9c8; margin: .55rem 0 0; }
    .sidebar-footer {
        border-top: 1px solid #17283b; color: #9eabba; font-size: .72rem;
        margin-top: 5rem; padding-top: 1rem;
    }
    [data-testid="stButtonGroup"] { display: flex; justify-content: flex-end; }
    [data-testid="stButtonGroup"] button {
        background: rgba(7,18,32,.88); border-color: #26364a; color: #edf4fb;
        font-size: .9rem; height: 3.25rem; min-height: 3.25rem; padding: .7rem 1rem;
    }
    [data-testid="stButtonGroup"] button[aria-checked="true"] {
        background: rgba(10,42,48,.76); border-color: #00cdbd; color: #20e0cf;
    }
    [data-testid="stMain"] [data-testid="stButton"] button,
    [data-testid="stMain"] [data-testid="stPopover"] button {
        background: rgba(7,18,32,.88); border: 1px solid #26364a;
        color: #edf4fb; min-height: 3.2rem;
    }
    [data-testid="stMain"] [data-testid="stDateInput"] input {
        font-size: .9rem; min-height: 3.2rem;
    }
    [data-testid="stMain"] [data-testid="stBaseButton-primary"] {
        background: rgba(10,42,48,.76); border-color: #00cdbd; color: #20e0cf;
    }
    .section-heading { margin: .55rem 0 .2rem; }
    .section-heading h2 { font-size: 1.9rem; letter-spacing: -.025em; }
    .section-heading p { color: #b7c2d0; font-size: .9rem; }
    .kpi-grid { gap: .9rem; margin: 1.05rem 0 .85rem; }
    .kpi-card {
        background: linear-gradient(145deg, rgba(10,22,37,.98), rgba(8,18,31,.98));
        border-color: #1a2b3f; border-radius: .65rem; min-height: 5.4rem; padding: 1rem 1.15rem;
    }
    .kpi-value { font-size: 1.55rem; }
    .kpi-label { color: #aab6c5; }
    .card-grid { gap: .9rem; }
    .programme-card {
        background: linear-gradient(180deg, #0a1727, #091523); border-color: #1a2b3e;
        border-radius: .7rem; box-shadow: none; padding: .4rem .55rem .65rem;
    }
    .poster-frame { aspect-ratio: 1.15 / 1; border-radius: .35rem; }
    .rank-badge { border: 1px solid currentColor; border-radius: .35rem; font-size: 1rem; }
    .channel-badge { background: #07111d; border-radius: .35rem; }
    .card-grid .programme-card:nth-child(1) { --rank-accent: #19d4bd; }
    .card-grid .programme-card:nth-child(2) { --rank-accent: #258cf5; }
    .card-grid .programme-card:nth-child(3) { --rank-accent: #ffab19; }
    .card-grid .programme-card:nth-child(4) { --rank-accent: #a855f7; }
    .card-grid .programme-card .rank-badge {
        background: color-mix(in srgb, var(--rank-accent) 25%, #07111d);
        color: var(--rank-accent);
    }
    .card-grid .programme-card .metric-number { color: var(--rank-accent); }
    .card-grid .programme-card .evidence-fill { background: var(--rank-accent); }
    .programme-heading { font-size: .98rem; margin-top: .65rem; }
    .programme-details, .programme-meta { color: #b1bdcc; }
    .programme-meta .rating-star { display: none; }
    .programme-meta { min-height: 1.4rem; }
    .dual-metric { border-color: #1a2b3e; }
    .metric-number small { color: #aab6c5; font-size: .72rem; font-weight: 400; }
    .why-title { background: #101e30; border-color: #203147; }
    .evidence-row { margin: .55rem .15rem; }
    .card-cta {
        border: 1px solid #203147; border-radius: .4rem; color: #c2cddb;
        margin-top: .75rem; padding: .55rem .7rem;
    }
    .continuation { background: #091625; border-color: #1a2b3e; }
    .continuation .cta-button {
        border: 1px solid #00bcae; border-radius: .45rem; color: #20e0cf;
        font-size: .82rem; font-weight: 700; min-width: 14rem; padding: .72rem 1rem;
        text-align: center;
    }
    </style>
    """
)


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


@st.cache_data(ttl=3600)
def load_channel_logos() -> dict[str, str]:
    """Return live source-owned logo URLs keyed by channel display name."""
    try:
        catalog = ScheduleClient(timeout=5.0, max_attempts=1).fetch_catalog()
    except (ChannelCatalogError, httpx.HTTPError):
        return {}
    return {
        channel.display_name: channel.logo_url
        for channel in catalog
        if channel.logo_url is not None
    }


@st.cache_data(ttl=60)
def load_dates(
    database_path: str,
    database_modified_at: float,
    source: str,
    channel: str | None,
) -> list[date]:
    """Load archived dates for a source and channel."""
    del database_modified_at
    return available_dates(Path(database_path), source, channel)


@st.cache_data(ttl=60)
def load_highlights(
    database_path: str,
    database_modified_at: float,
    source: str,
    channels: tuple[str, ...],
    schedule_dates: tuple[date, ...],
    limit_per_day: int,
) -> list[dict[str, object]]:
    """Load ranked highlights for every date in the active viewing horizon."""
    del database_modified_at
    return [
        highlight
        for schedule_date in schedule_dates
        for highlight in daily_highlights(
            Path(database_path),
            source,
            list(channels),
            schedule_date,
            limit_per_day,
        )
    ]


def stop_with_error(message: str) -> None:
    """Render an actionable error and stop the current Streamlit run."""
    st.error(message)
    st.stop()


def set_all_channels(channels: list[str], selected: bool) -> None:
    """Update every channel checkbox before Streamlit renders the next run."""
    for channel_name in channels:
        st.session_state[f"channel_{channel_name}"] = selected


def activate_quick_window() -> None:
    """Copy the native quick-window selection into the active view."""
    selected_window = st.session_state.get("quick_viewing_window")
    if selected_window:
        st.session_state["active_viewing_window"] = selected_window


def poster_markup(
    image_url: str | None,
    title: str,
    rank: int,
    channel: str,
) -> str:
    """Return a fixed-size editorial poster with rank and channel badges."""
    source = escape(image_url or POSTER_PLACEHOLDER_URI, quote=True)
    alternative_text = escape(f"Poster for {title}", quote=True)
    return (
        '<div class="poster-frame">'
        f'<span class="rank-badge">{rank}</span>'
        f'<span class="channel-badge">{escape(channel)}</span>'
        f'<img src="{source}" alt="{alternative_text}" loading="lazy" draggable="false">'
        "</div>"
    )


def evidence_markup(highlight: dict[str, object], show_technical_details: bool) -> str:
    """Return compact visual evidence for one ranking decision."""
    components = (
        ("Quality", float(highlight["quality_score"]), "70% weight"),
        ("Vote confidence", float(highlight["confidence_score"]), "20% weight"),
        ("Popularity", float(highlight["popularity_score"]), "10% weight"),
    )
    rows = "".join(
        (
            '<div class="evidence-row">'
            '<div class="evidence-label">'
            f"<span>{label} · {weight}</span><strong>{score:.1f}</strong>"
            "</div>"
            '<div class="evidence-track">'
            f'<div class="evidence-fill" style="width:{min(100.0, max(0.0, score)):.1f}%"></div>'
            "</div></div>"
        )
        for label, score, weight in components
    )
    if not show_technical_details:
        return rows
    return rows + (
        '<div class="evidence-meta">'
        f"TMDB votes: {highlight['vote_count'] or 0:,}<br>"
        f"TMDB ID: {highlight['tmdb_id']} · IMDb ID: "
        f"{escape(str(highlight['imdb_id'] or 'Not available'))}<br>"
        f"Metrics observed: {escape(str(highlight['metrics_observed_at']))}<br>"
        f"Metadata retrieved: {escape(str(highlight['metadata_retrieved_at']))}"
        "</div>"
    )


def programme_metadata(highlight: dict[str, object]) -> str:
    """Format compact audience-facing programme metadata."""
    try:
        genres = json.loads(str(highlight["genres_json"]))
    except (TypeError, ValueError, json.JSONDecodeError):
        genres = []
    parts = [", ".join(str(genre) for genre in genres[:2])]
    if highlight["release_year"]:
        parts.append(str(highlight["release_year"]))
    if highlight["runtime_minutes"]:
        minutes = int(highlight["runtime_minutes"])
        parts.append(f"{minutes // 60}h {minutes % 60}m" if minutes >= 60 else f"{minutes}m")
    return " · ".join(part for part in parts if part)


def card_markup(highlight: dict[str, object], show_technical_details: bool) -> str:
    """Return one complete poster card, linked to IMDb when identity is available."""
    title = str(highlight["programme_title"] or highlight["schedule_title"])
    channel = str(highlight["channel"])
    start_time = highlight["starts_at_local"].strftime("%H:%M")
    image = poster_url(highlight["poster_path"])
    destination = imdb_url(highlight["imdb_id"])
    match_confidence = highlight["match_confidence"]
    match_label = f"{float(match_confidence):.0f}%" if match_confidence is not None else "—"
    if destination:
        opening = (
            f'<a class="programme-card" href="{escape(destination, quote=True)}" '
            f'target="_blank" rel="noopener noreferrer" aria-label="View {escape(title)} on IMDb">'
        )
        closing = "</a>"
        call_to_action = '<div class="card-cta"><span>More details</span><span>ⓘ</span></div>'
    else:
        opening = '<article class="programme-card unavailable">'
        closing = "</article>"
        call_to_action = '<div class="card-cta"><span>IMDb page unavailable</span></div>'

    return (
        opening
        + poster_markup(
            image,
            title,
            int(highlight["highlight_rank"]),
            channel,
        )
        + '<div class="programme-heading">'
        + escape(title)
        + "</div>"
        + '<div class="programme-details">'
        + f"◷ {escape(start_time)} &nbsp;•&nbsp; {escape(channel)}"
        + "</div>"
        + f'<div class="programme-meta">{escape(programme_metadata(highlight))}</div>'
        + '<div class="dual-metric"><div><div class="metric-name">Pick Score</div>'
        + '<div class="metric-number">'
        + f"{highlight['highlight_score']:.1f}<small>/100</small></div></div>"
        + '<div><div class="metric-name">Match Confidence</div>'
        + f'<div class="metric-number">{match_label}</div></div></div>'
        + '<div class="why-title">⌄ &nbsp; Why this pick?</div>'
        + evidence_markup(highlight, show_technical_details)
        + call_to_action
        + closing
    )


database_path = DEFAULT_DATABASE_PATH.expanduser().resolve()
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
    source = sources[0]

    channels = load_channels(str(database_path), database_modified_at, source)
    if not channels:
        stop_with_error("No channels with eligible highlights were found for this source.")
    channels.sort(key=lambda value: (CHANNEL_PRIORITY.get(value, 100), value.casefold()))
    channel_logos = load_channel_logos()
    with st.sidebar:
        st.html(
            '<div class="sidebar-brand"><span class="tv-mark">⌁</span>'
            "<span>Greek TV<br>Highlights Radar</span></div>"
            '<div class="sidebar-label">Channels</div>'
            '<div class="all-channel-row">⌁ &nbsp; All channels</div>'
        )
        selected_channels = []
        for channel_name in channels:
            option_column, logo_column, name_column = st.columns(
                [0.65, 1, 3.35],
                gap="small",
                vertical_alignment="center",
            )
            if option_column.checkbox(
                channel_name,
                value=True,
                key=f"channel_{channel_name}",
                label_visibility="collapsed",
            ):
                selected_channels.append(channel_name)
            logo_url = channel_logos.get(channel_name)
            if logo_url:
                logo_column.html(
                    '<div class="channel-logo-frame">'
                    f'<img src="{escape(logo_url, quote=True)}" '
                    f'alt="{escape(channel_name, quote=True)} logo">'
                    "</div>"
                )
            else:
                logo_column.html('<div class="channel-logo-frame">◇</div>')
            name_column.html(f'<div class="channel-name">{escape(channel_name.upper())}</div>')
        action_columns = st.columns(2)
        action_columns[0].button(
            "◉ Select all",
            width="stretch",
            on_click=set_all_channels,
            args=(channels, True),
        )
        action_columns[1].button(
            "ⓧ Clear all",
            width="stretch",
            on_click=set_all_channels,
            args=(channels, False),
        )
        st.html(
            '<section class="about-card"><strong>ⓘ &nbsp; About this radar</strong>'
            "<p>Greek TV schedules are enriched with movie and TV metadata and "
            "ranked to surface the most interesting programmes.</p>"
            '<p class="tmdb-credit">Metadata and posters: TMDB. Not endorsed or certified '
            "by TMDB.</p></section>"
        )

    dates = load_dates(str(database_path), database_modified_at, source, None)
    if not dates:
        stop_with_error("No archived highlight dates were found for this channel selection.")
    today = datetime.now(ATHENS_TIMEZONE).date()
    historical_dates = [available_date for available_date in dates if available_date < today]
    if not historical_dates:
        stop_with_error("No historical schedule dates are available yet.")
    if "active_viewing_window" not in st.session_state:
        st.session_state["active_viewing_window"] = "Tonight"
    if "quick_viewing_window" not in st.session_state:
        st.session_state["quick_viewing_window"] = "Tonight"

    header_left, header_right = st.columns([2.35, 2.65])
    header_right.segmented_control(
        "Schedule window",
        [*VIEWING_HORIZONS, ARCHIVE_VIEW],
        key="quick_viewing_window",
        label_visibility="collapsed",
        width="stretch",
        on_change=activate_quick_window,
        format_func=lambda option: "📅 Custom date" if option == ARCHIVE_VIEW else option,
    )

    viewing_window = st.session_state["active_viewing_window"]
    if viewing_window == ARCHIVE_VIEW:
        archive_date = header_right.date_input(
            "Historical broadcast date",
            value=max(historical_dates),
            min_value=min(historical_dates),
            max_value=today - timedelta(days=1),
            help="Archive dates stop at yesterday because current and future schedules may change.",
            format="DD/MM/YYYY",
            key="historical_broadcast_date",
        )
        selected_dates = (archive_date,)
    elif viewing_window == "Tomorrow":
        selected_dates = tuple(dates_in_horizon(dates, today + timedelta(days=1), 1))
    else:
        selected_dates = tuple(
            sorted(dates_in_horizon(dates, today, VIEWING_HORIZONS[viewing_window]))
        )

    highlights = (
        load_highlights(
            str(database_path),
            database_modified_at,
            source,
            tuple(selected_channels),
            selected_dates,
            4,
        )
        if selected_channels
        else []
    )
except DashboardDataError as error:
    stop_with_error(str(error))

show_technical_details = False
view_title = {
    "Tonight": "Tonight's Top Picks",
    "Tomorrow": "Tomorrow's Top Picks",
    "Next 3 days": "Top Picks for the Next 3 Days",
    ARCHIVE_VIEW: "Top Picks for the Selected Date",
}[str(viewing_window)]
if selected_dates:
    range_label = (
        f"{selected_dates[0]:%A, %d %B %Y}"
        if len(selected_dates) == 1
        else f"{selected_dates[0]:%d %b} – {selected_dates[-1]:%d %b %Y}"
    )
else:
    range_label = f"from {today:%d %b %Y}"
header_left.html(
    '<div class="section-heading"><div>'
    f"<h2>🌙 {escape(view_title)}</h2>"
    f"<p>▣ &nbsp; {escape(range_label)}</p>"
    "</div></div>"
)

if not highlights:
    st.html(
        '<section class="empty-state">'
        "<h3>No picks are ready for this window yet</h3>"
        "<p>Use the historical date field above to explore an ingested date, or enrich the "
        "upcoming schedules to publish fresh recommendations.</p>"
        "</section>"
    )
    st.stop()

top_highlight = highlights[0]
represented_channels = len({str(highlight["channel"]) for highlight in highlights})
last_updated = max(highlight["metrics_observed_at"] for highlight in highlights)
st.sidebar.html(
    f'<div class="sidebar-footer">Last updated: {last_updated:%d %b %Y, %H:%M} &nbsp; ⟳</div>'
)
st.html(
    f'<p style="color:var(--muted)">{len(highlights)} programmes worth watching '
    f"across {represented_channels} channel{'s' if represented_channels != 1 else ''}.</p>"
    '<div class="kpi-grid">'
    '<div class="kpi-card"><span class="kpi-icon">🎬</span><div>'
    f'<div class="kpi-value">{len(highlights)}</div>'
    '<div class="kpi-label">Top Picks</div></div></div>'
    '<div class="kpi-card"><span class="kpi-icon">📺</span><div>'
    f'<div class="kpi-value">{represented_channels}</div>'
    '<div class="kpi-label">Channels</div></div></div>'
    '<div class="kpi-card"><span class="kpi-icon rating-star">★</span><div>'
    f'<div class="kpi-value">{top_highlight["highlight_score"]:.1f}</div>'
    '<div class="kpi-label">Top Pick Score</div></div></div>'
    '<div class="kpi-card"><span class="kpi-icon">🛡</span><div>'
    f'<div class="kpi-value">{escape(str(top_highlight["ranking_version"]))}</div>'
    '<div class="kpi-label">Policy Version</div></div></div>'
    "</div>"
)

for schedule_date in selected_dates:
    daily_results = [
        highlight for highlight in highlights if highlight["schedule_date"] == schedule_date
    ]
    if not daily_results:
        continue
    if len(selected_dates) > 1:
        st.html(
            '<div class="section-heading"><div>'
            f"<h2>{schedule_date:%A}</h2>"
            f"<p>{schedule_date:%d %B %Y} · {len(daily_results)} picks</p>"
            "</div></div>"
        )
    st.html(
        '<div class="card-grid">'
        + "".join(card_markup(highlight, show_technical_details) for highlight in daily_results)
        + "</div>"
    )

st.html(
    '<section class="continuation"><div><strong>🎬 More upcoming highlights</strong><br>'
    "<span>See what's worth watching in the next 3 days.</span></div>"
    '<span class="cta-button">View full schedule &nbsp; ›</span></section>'
)
