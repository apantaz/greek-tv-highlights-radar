from collections.abc import Iterable
from pathlib import Path

import duckdb

from greek_tv.models import Broadcast


class BroadcastRepository:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path

    def initialize(self) -> None:
        with duckdb.connect(str(self.path)) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS broadcasts (
                    broadcast_id VARCHAR PRIMARY KEY,
                    channel VARCHAR NOT NULL,
                    title VARCHAR NOT NULL,
                    starts_at TIMESTAMPTZ NOT NULL,
                    ends_at TIMESTAMPTZ,
                    description VARCHAR,
                    source_url VARCHAR NOT NULL,
                    retrieved_at TIMESTAMPTZ NOT NULL
                )
                """
            )

    def upsert(self, broadcasts: Iterable[Broadcast]) -> int:
        records = list(broadcasts)
        self.initialize()
        with duckdb.connect(str(self.path)) as connection:
            connection.executemany(
                """
                INSERT INTO broadcasts VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (broadcast_id) DO UPDATE SET
                    ends_at = excluded.ends_at,
                    description = excluded.description,
                    retrieved_at = excluded.retrieved_at
                """,
                [
                    (
                        item.broadcast_id,
                        item.channel,
                        item.title,
                        item.starts_at,
                        item.ends_at,
                        item.description,
                        item.source_url,
                        item.retrieved_at,
                    )
                    for item in records
                ],
            )
        return len(records)

    def count(self) -> int:
        self.initialize()
        with duckdb.connect(str(self.path), read_only=True) as connection:
            return connection.execute("SELECT count(*) FROM broadcasts").fetchone()[0]
