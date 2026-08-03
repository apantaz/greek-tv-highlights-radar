from datetime import date

import duckdb

from greek_tv.enrichment import (
    TmdbCandidate,
    TmdbCandidateRepository,
    TmdbEntityDetails,
    TmdbSearchResponse,
    extract_title_evidence,
)
from greek_tv.enrichment.entity_batch import EntityEnrichmentStatus, enrich_matched_entities


class FakeDetailsClient:
    def __init__(self, failing_ids: set[int] | None = None) -> None:
        self.failing_ids = failing_ids or set()
        self.requests = []

    def details(self, media_type: str, tmdb_id: int, language: str) -> TmdbEntityDetails:
        self.requests.append((media_type, tmdb_id, language))
        if tmdb_id in self.failing_ids:
            raise RuntimeError("TMDB unavailable")
        return TmdbEntityDetails(
            tmdb_id=tmdb_id,
            media_type=media_type,
            language=language,
            title=f"Entity {tmdb_id}",
            original_title=f"Entity {tmdb_id}",
            original_language="en",
            release_date=date(2020, 1, 1),
            overview=None,
            tagline=None,
            runtime_minutes=90,
            status="Released",
            homepage=None,
            imdb_id=f"tt{tmdb_id:07d}",
            genres=("Drama",),
            production_countries=("US",),
            production_companies=(),
            spoken_languages=("en",),
            popularity=12.5,
            vote_average=7.5,
            vote_count=100,
            payload={"id": tmdb_id},
        )


def add_matched_resolution(path, tmdb_id: int) -> None:
    repository = TmdbCandidateRepository(path)
    response = TmdbSearchResponse(
        {"results": []},
        (
            TmdbCandidate(
                1,
                tmdb_id,
                "movie",
                f"Entity {tmdb_id}",
                f"Entity {tmdb_id}",
                "en",
                date(2020, 1, 1),
                None,
                None,
                None,
                None,
            ),
        ),
    )
    search = repository.save(f"entity {tmdb_id}", f"Entity {tmdb_id}", "el-GR", response)
    evidence = extract_title_evidence(f"Entity {tmdb_id}", "Production year: 2020")
    lookup = repository.record_lookup(evidence, search.search_id, used_query_override=False)
    repository.resolve_lookup(lookup.lookup_id)


def test_retrieves_matched_entities_and_reuses_cache(tmp_path):
    path = tmp_path / "entities.duckdb"
    add_matched_resolution(path, 11)
    client = FakeDetailsClient()

    first = enrich_matched_entities(path, language="el-GR", client_factory=lambda: client)
    second = enrich_matched_entities(path, language="el-GR", client_factory=lambda: client)

    assert first.count(EntityEnrichmentStatus.RETRIEVED) == 1
    assert second.count(EntityEnrichmentStatus.CACHED) == 1
    assert client.requests == [("movie", 11, "el-GR")]
    with duckdb.connect(str(path), read_only=True) as connection:
        assert connection.execute("select count(*) from tmdb_entity_details").fetchone()[0] == 1


def test_isolates_entity_failures_and_continues(tmp_path):
    path = tmp_path / "entities.duckdb"
    add_matched_resolution(path, 11)
    add_matched_resolution(path, 12)
    client = FakeDetailsClient({11})

    result = enrich_matched_entities(path, language="el-GR", client_factory=lambda: client)

    assert result.failed == 1
    assert result.count(EntityEnrichmentStatus.RETRIEVED) == 1
    assert result.entities[0].error_message == "RuntimeError: TMDB unavailable"
