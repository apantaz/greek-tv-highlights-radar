import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "greek_tv.duckdb"
DEFAULT_RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def database_path() -> Path:
    return Path(os.getenv("DUCKDB_PATH", DEFAULT_DATABASE_PATH))


def raw_data_dir() -> Path:
    return Path(os.getenv("RAW_DATA_DIR", DEFAULT_RAW_DATA_DIR))


def http_timeout_seconds() -> float:
    return float(os.getenv("HTTP_TIMEOUT_SECONDS", "20"))


def http_max_attempts() -> int:
    return int(os.getenv("HTTP_MAX_ATTEMPTS", "3"))


def minimum_schedule_records() -> int:
    return int(os.getenv("MINIMUM_SCHEDULE_RECORDS", "5"))


def tmdb_access_token() -> str:
    """Return the private TMDB read-access token or fail with setup guidance."""
    token = os.getenv("TMDB_API_TOKEN", "").strip()
    if not token:
        raise ValueError("TMDB_API_TOKEN is required for TMDB searches")
    return token
