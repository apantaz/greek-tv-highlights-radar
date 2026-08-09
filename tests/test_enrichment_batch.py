from datetime import date

import duckdb

from greek_tv.enrichment import TmdbCandidate, TmdbCandidateRepository, TmdbSearchResponse
from greek_tv.enrichment.batch import BatchEnrichmentStatus, enrich_current_programmes


class FakeTmdbClient:
    def __init__(self, failing_queries: set[str] | None = None) -> None:
        self.failing_queries = failing_queries or set()
        self.queries = []

    def search(self, query: str, language: str) -> TmdbSearchResponse:
        self.queries.append((query, language))
        if query in self.failing_queries:
            raise RuntimeError("TMDB unavailable")
        year = 2007 if "Harry Potter" in query else 2020
        candidate = TmdbCandidate(
            rank=1,
            tmdb_id=len(self.queries),
            media_type="movie",
            title=query,
            original_title=query,
            original_language="en",
            release_date=date(year, 1, 1),
            overview=None,
            popularity=None,
            vote_average=None,
            vote_count=None,
        )
        return TmdbSearchResponse({"page": 1, "results": []}, (candidate,))


def create_current_programmes(path, rows):
    TmdbCandidateRepository(path).initialize()
    with duckdb.connect(str(path)) as connection:
        connection.execute(
            """
            create table ingestion_runs (
                run_id varchar primary key,
                source varchar not null,
                channel varchar not null,
                schedule_date date not null,
                source_url varchar not null,
                started_at timestamptz not null,
                completed_at timestamptz,
                status varchar not null,
                records_parsed integer not null,
                snapshot_path varchar,
                error_message varchar
            )
            """
        )
        connection.execute(
            """
            insert into ingestion_runs values (
                'run-star', 'programmatileorasis', 'STAR', '2026-08-01',
                'https://example.test/star', now(), now(), 'succeeded', ?, null, null
            )
            """,
            [len(rows)],
        )
        connection.execute(
            """
            create table broadcast_observations (
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
        observations = [f"obs-{index}" for index in range(1, len(rows) + 1)]
        connection.executemany(
            """
            insert into broadcast_observations values (
                ?, 'run-star', ?, 'STAR', ?, '2026-08-01 20:00:00+03', null,
                ?, 'https://example.test/star', now()
            )
            """,
            [
                (observation_id, f"broadcast-{index}", title, description)
                for index, (observation_id, (title, description)) in enumerate(
                    zip(observations, rows, strict=True), start=1
                )
            ],
        )


def test_enriches_distinct_programmes_and_skips_equivalent_evidence_on_next_run(tmp_path):
    path = tmp_path / "batch.duckdb"
    title = "Ο Χάρι Πότερ (Harry Potter)"
    description = "Αμερικανικής παραγωγής 2007."
    create_current_programmes(path, [(title, description), (title, description)])
    client = FakeTmdbClient()

    first = enrich_current_programmes(
        path,
        language="el-GR",
        client_factory=lambda: client,
    )
    second = enrich_current_programmes(
        path,
        language="el-GR",
        client_factory=lambda: client,
    )

    assert first.total == 1
    assert first.count(BatchEnrichmentStatus.MATCHED) == 1
    assert first.retrieved == 1
    assert second.count(BatchEnrichmentStatus.SKIPPED) == 1
    assert client.queries == [("Harry Potter", "el-GR")]
    with duckdb.connect(str(path), read_only=True) as connection:
        links = connection.execute(
            "select observation_id, language from broadcast_enrichment_lookups order by 1"
        ).fetchall()
    assert links == [("obs-1", "el-GR"), ("obs-2", "el-GR")]


def test_isolates_title_failures_and_continues_batch(tmp_path):
    path = tmp_path / "batch.duckdb"
    create_current_programmes(
        path,
        [
            ("Broken", None),
            ("Working", "Αμερικανικής παραγωγής 2020."),
        ],
    )
    client = FakeTmdbClient({"Broken"})

    result = enrich_current_programmes(
        path,
        language="el-GR",
        client_factory=lambda: client,
    )

    assert result.total == 2
    assert result.failed == 1
    assert result.count(BatchEnrichmentStatus.MATCHED) == 1
    assert result.programmes[0].error_message == "RuntimeError: TMDB unavailable"
    assert client.queries == [("Broken", "el-GR"), ("Working", "el-GR")]


def test_reports_each_programme_as_soon_as_it_completes(tmp_path):
    path = tmp_path / "batch.duckdb"
    create_current_programmes(path, [("First", None), ("Second", None)])
    client = FakeTmdbClient()
    reported = []

    result = enrich_current_programmes(
        path,
        language="el-GR",
        client_factory=lambda: client,
        on_programme=lambda item, completed, total: reported.append((item, completed, total)),
    )

    assert reported == [
        (result.programmes[0], 1, 2),
        (result.programmes[1], 2, 2),
    ]
    assert [item.source_title for item, _, _ in reported] == ["First", "Second"]


def test_filters_current_programmes_by_channel_and_schedule_date(tmp_path):
    path = tmp_path / "batch.duckdb"
    create_current_programmes(path, [("STAR Programme", None)])
    with duckdb.connect(str(path)) as connection:
        connection.execute(
            """
            insert into ingestion_runs values (
                'run-ert', 'programmatileorasis', 'ΕΡΤ1', '2026-08-02',
                'https://example.test/ert', now(), now(), 'succeeded', 1, null, null
            )
            """
        )
        connection.execute(
            """
            insert into broadcast_observations values (
                'obs-ert', 'run-ert', 'broadcast-ert', 'ΕΡΤ1', 'ERT Programme',
                '2026-08-02 20:00:00+03', null, null,
                'https://example.test/ert', now()
            )
            """
        )
    client = FakeTmdbClient()

    result = enrich_current_programmes(
        path,
        language="el-GR",
        client_factory=lambda: client,
        channel="star",
        schedule_date=date(2026, 8, 1),
    )

    assert result.total == 1
    assert result.programmes[0].source_title == "STAR Programme"
    assert client.queries == [("STAR Programme", "el-GR")]
