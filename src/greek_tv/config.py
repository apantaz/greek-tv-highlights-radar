import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "greek_tv.duckdb"
DEFAULT_RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def database_path() -> Path:
    return Path(os.getenv("DUCKDB_PATH", DEFAULT_DATABASE_PATH))


def raw_data_dir() -> Path:
    return Path(os.getenv("RAW_DATA_DIR", DEFAULT_RAW_DATA_DIR))
