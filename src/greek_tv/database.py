"""DuckDB persistence for immutable ingestion runs and schedule observations."""

from collections.abc import Iterable
from datetime import UTC, date, datetime
from hashlib import sha256
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import duckdb

from greek_tv.models import Broadcast, IngestionRun, IngestionStatus

SOURCE_NAME = "programmatileorasis"


class IngestionRepository:
    """Persist ingestion audit metadata and append-only broadcast observations."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path

    def initialize(self) -> None:
        """Create the current schema and non-destructively migrate legacy broadcasts."""
        with duckdb.connect(str(self.path)) as connection:
            connection.execute(
                """
                create table if not exists ingestion_runs (
                    run_id varchar primary key,
                    source varchar not null,
                    channel varchar not null,
                    schedule_date date not null,
                    source_url varchar not null,
                    started_at timestamptz not null,
                    completed_at timestamptz,
                    status varchar not null,
                    records_parsed integer not null default 0,
                    snapshot_path varchar,
                    error_message varchar,
                    check (status in ('running', 'succeeded', 'failed'))
                )
                """
            )
            connection.execute(
                """
                create table if not exists broadcast_observations (
                    observation_id varchar primary key,
                    run_id varchar not null,
                    broadcast_id varchar not null,
                    channel varchar not null,
                    title varchar not null,
                    starts_at timestamptz not null,
                    ends_at timestamptz,
                    description varchar,
                    source_url varchar not null,
                    retrieved_at timestamptz not null,
                    foreign key (run_id) references ingestion_runs(run_id)
                )
                """
            )
            self._migrate_legacy_broadcasts(connection)
            connection.execute(
                """
                create or replace view current_broadcasts as
                with ranked_runs as (
                    select
                        run_id,
                        row_number() over (
                            partition by source, channel, schedule_date
                            order by completed_at desc, started_at desc, run_id desc
                        ) as run_rank
                    from ingestion_runs
                    where status = 'succeeded'
                )
                select
                    observations.broadcast_id,
                    observations.channel,
                    observations.title,
                    observations.starts_at,
                    observations.ends_at,
                    observations.description,
                    observations.source_url,
                    observations.retrieved_at,
                    observations.run_id
                from broadcast_observations as observations
                inner join ranked_runs using (run_id)
                where ranked_runs.run_rank = 1
                """
            )

    def start_run(self, run: IngestionRun) -> None:
        """Record a run before any network or parsing work begins."""
        self.initialize()
        with duckdb.connect(str(self.path)) as connection:
            connection.execute(
                """
                insert into ingestion_runs (
                    run_id, source, channel, schedule_date, source_url, started_at,
                    completed_at, status, records_parsed, snapshot_path, error_message
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    run.run_id,
                    run.source,
                    run.channel,
                    run.schedule_date,
                    run.source_url,
                    run.started_at,
                    run.completed_at,
                    run.status.value,
                    run.records_parsed,
                    run.snapshot_path,
                    run.error_message,
                ],
            )

    def complete_run(
        self,
        run_id: str,
        broadcasts: Iterable[Broadcast],
        snapshot_path: Path,
        completed_at: datetime,
    ) -> int:
        """Atomically append observations and mark their run successful."""
        records = list(broadcasts)
        with duckdb.connect(str(self.path)) as connection:
            connection.begin()
            try:
                connection.executemany(
                    """
                    insert into broadcast_observations (
                        observation_id, run_id, broadcast_id, channel, title, starts_at,
                        ends_at, description, source_url, retrieved_at
                    ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            _observation_id(run_id, item.broadcast_id),
                            run_id,
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
                connection.execute(
                    """
                    update ingestion_runs
                    set status = ?, completed_at = ?, records_parsed = ?, snapshot_path = ?
                    where run_id = ? and status = ?
                    """,
                    [
                        IngestionStatus.SUCCEEDED.value,
                        completed_at,
                        len(records),
                        str(snapshot_path),
                        run_id,
                        IngestionStatus.RUNNING.value,
                    ],
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return len(records)

    def fail_run(
        self,
        run_id: str,
        error: Exception,
        completed_at: datetime,
        snapshot_path: Path | None = None,
    ) -> None:
        """Mark a started run failed while retaining a concise error message."""
        message = f"{type(error).__name__}: {error}"[:2000]
        with duckdb.connect(str(self.path)) as connection:
            connection.execute(
                """
                update ingestion_runs
                set status = ?, completed_at = ?, error_message = ?, snapshot_path = ?
                where run_id = ? and status = ?
                """,
                [
                    IngestionStatus.FAILED.value,
                    completed_at,
                    message,
                    str(snapshot_path) if snapshot_path else None,
                    run_id,
                    IngestionStatus.RUNNING.value,
                ],
            )

    def get_run(self, run_id: str) -> IngestionRun:
        """Return one persisted run."""
        self.initialize()
        with duckdb.connect(str(self.path), read_only=True) as connection:
            row = connection.execute(
                """
                select
                    run_id, source, channel, schedule_date, source_url, started_at,
                    completed_at, status, records_parsed, snapshot_path, error_message
                from ingestion_runs
                where run_id = ?
                """,
                [run_id],
            ).fetchone()
        if row is None:
            raise KeyError(f"ingestion run {run_id!r} was not found")
        return IngestionRun.model_validate(dict(zip(IngestionRun.model_fields, row, strict=True)))

    def count(self, table: str = "current_broadcasts") -> int:
        """Count rows in a known public relation, primarily for diagnostics and tests."""
        allowed = {"broadcast_observations", "current_broadcasts", "ingestion_runs"}
        if table not in allowed:
            raise ValueError(f"unsupported relation {table!r}")
        self.initialize()
        with duckdb.connect(str(self.path), read_only=True) as connection:
            return connection.execute(f"select count(*) from {table}").fetchone()[0]

    def _migrate_legacy_broadcasts(self, connection: duckdb.DuckDBPyConnection) -> None:
        tables = {row[0] for row in connection.execute("show tables").fetchall()}
        if "broadcasts" not in tables:
            return

        rows = connection.execute(
            """
            select
                broadcast_id, channel, title, starts_at, ends_at, description,
                source_url, retrieved_at
            from broadcasts
            order by retrieved_at, channel, source_url, starts_at
            """
        ).fetchall()
        groups: dict[tuple[str, str, datetime], list[tuple]] = {}
        for row in rows:
            groups.setdefault((row[1], row[6], row[7]), []).append(row)

        for (channel, source_url, retrieved_at), broadcasts in groups.items():
            run_id = _legacy_run_id(channel, source_url, retrieved_at)
            schedule_date = _schedule_date(source_url, broadcasts[0][3])
            connection.execute(
                """
                insert into ingestion_runs (
                    run_id, source, channel, schedule_date, source_url, started_at,
                    completed_at, status, records_parsed, snapshot_path, error_message
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict (run_id) do nothing
                """,
                [
                    run_id,
                    SOURCE_NAME,
                    channel,
                    schedule_date,
                    source_url,
                    retrieved_at,
                    retrieved_at,
                    IngestionStatus.SUCCEEDED.value,
                    len(broadcasts),
                    None,
                    None,
                ],
            )
            connection.executemany(
                """
                insert into broadcast_observations (
                    observation_id, run_id, broadcast_id, channel, title, starts_at,
                    ends_at, description, source_url, retrieved_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict (observation_id) do nothing
                """,
                [
                    (
                        _observation_id(run_id, row[0]),
                        run_id,
                        *row,
                    )
                    for row in broadcasts
                ],
            )


def _observation_id(run_id: str, broadcast_id: str) -> str:
    return sha256(f"{run_id}|{broadcast_id}".encode()).hexdigest()


def _legacy_run_id(channel: str, source_url: str, retrieved_at: datetime) -> str:
    identity = f"legacy|{channel}|{source_url}|{retrieved_at.isoformat()}"
    return f"legacy-{sha256(identity.encode()).hexdigest()[:24]}"


def _schedule_date(source_url: str, starts_at: datetime) -> date:
    query_date = parse_qs(urlparse(source_url).query).get("date", [None])[0]
    if query_date:
        try:
            return date.fromisoformat(query_date)
        except ValueError:
            pass
    return starts_at.astimezone(UTC).date()
