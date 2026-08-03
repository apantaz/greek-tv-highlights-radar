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
        connection.execute("create table current_broadcasts (title varchar, description varchar)")
        connection.executemany("insert into current_broadcasts values (?, ?)", rows)


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
