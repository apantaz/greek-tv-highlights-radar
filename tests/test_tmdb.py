from datetime import UTC, date, datetime

import duckdb
import httpx
import pytest

from greek_tv.enrichment import (
    TmdbCandidateRepository,
    TmdbClient,
    TmdbEntityRepository,
    extract_title_evidence,
)


def tmdb_payload():
    return {
        "page": 1,
        "results": [
            {
                "id": 11,
                "media_type": "movie",
                "title": "Star Wars",
                "original_title": "Star Wars",
                "original_language": "en",
                "release_date": "1977-05-25",
                "overview": "A space opera.",
                "popularity": 88.5,
                "vote_average": 8.2,
                "vote_count": 21000,
            },
            {
                "id": 1399,
                "media_type": "tv",
                "name": "Game of Thrones",
                "original_name": "Game of Thrones",
                "original_language": "en",
                "first_air_date": "2011-04-17",
                "overview": "A fantasy drama.",
                "popularity": 120.0,
                "vote_average": 8.5,
                "vote_count": 24000,
            },
            {"id": 1, "media_type": "person", "name": "Someone"},
        ],
        "total_pages": 1,
        "total_results": 3,
    }


def entity_payload():
    return {
        "id": 11,
        "title": "Star Wars",
        "original_title": "Star Wars",
        "original_language": "en",
        "release_date": "1977-05-25",
        "overview": "A space opera.",
        "tagline": "A long time ago...",
        "runtime": 121,
        "status": "Released",
        "homepage": "https://www.starwars.com/",
        "imdb_id": "tt0076759",
        "genres": [{"id": 12, "name": "Adventure"}],
        "production_countries": [{"iso_3166_1": "US", "name": "United States"}],
        "production_companies": [{"id": 1, "name": "Lucasfilm"}],
        "spoken_languages": [{"iso_639_1": "en", "english_name": "English"}],
        "popularity": 99.0,
        "vote_average": 8.2,
        "vote_count": 21000,
        "external_ids": {"imdb_id": "tt0076759"},
    }


def test_searches_with_bearer_token_and_parses_movie_and_tv_candidates():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer secret-token"
        assert request.url.params["query"] == "star wars"
        assert request.url.params["language"] == "el-GR"
        assert request.url.params["include_adult"] == "false"
        return httpx.Response(200, request=request, json=tmdb_payload())

    response = TmdbClient("secret-token", transport=httpx.MockTransport(handler)).search(
        "star wars"
    )

    assert [candidate.media_type for candidate in response.candidates] == ["movie", "tv"]
    assert response.candidates[0].tmdb_id == 11
    assert response.candidates[0].release_date == date(1977, 5, 25)
    assert response.candidates[1].rank == 2


def test_retries_transient_tmdb_responses():
    attempts = 0
    delays = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        status = 429 if attempts == 1 else 200
        return httpx.Response(status, request=request, json=tmdb_payload())

    client = TmdbClient(
        "token",
        max_attempts=2,
        backoff_seconds=0.25,
        transport=httpx.MockTransport(handler),
        sleep=delays.append,
    )

    client.search("title")

    assert attempts == 2
    assert delays == [0.25]


def test_retrieves_and_parses_matched_movie_details():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/3/movie/11"
        assert request.url.params["language"] == "el-GR"
        assert request.url.params["append_to_response"] == "external_ids"
        return httpx.Response(200, request=request, json=entity_payload())

    details = TmdbClient("token", transport=httpx.MockTransport(handler)).details("movie", 11)

    assert details.title == "Star Wars"
    assert details.runtime_minutes == 121
    assert details.imdb_id == "tt0076759"
    assert details.genres == ("Adventure",)
    assert details.production_countries == ("US",)
    assert details.production_companies == ("Lucasfilm",)
    assert details.spoken_languages == ("en",)


def test_rejects_blank_token_and_query():
    with pytest.raises(ValueError, match="token"):
        TmdbClient(" ")
    with pytest.raises(ValueError, match="query"):
        TmdbClient("token").search(" ")
    with pytest.raises(ValueError, match="media type"):
        TmdbClient("token").details("person", 1)


def test_persists_raw_response_and_reuses_latest_candidates(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, json=tmdb_payload())

    response = TmdbClient("token", transport=httpx.MockTransport(handler)).search("star wars")
    repository = TmdbCandidateRepository(tmp_path / "tmdb.duckdb")
    retrieved_at = datetime(2026, 8, 3, 10, tzinfo=UTC)

    saved = repository.save("star wars", "Star Wars", "el-GR", response, retrieved_at)
    cached = repository.latest("star wars", "el-GR")

    assert cached == saved
    assert cached is not None
    assert cached.search_query == "Star Wars"
    assert len(cached.candidates) == 2
    assert repository.latest("star wars", "en-US") is None


def test_caches_searches_with_no_supported_candidates(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            request=request,
            json={"page": 1, "results": [{"id": 1, "media_type": "person"}]},
        )

    response = TmdbClient("token", transport=httpx.MockTransport(handler)).search("unknown")
    repository = TmdbCandidateRepository(tmp_path / "tmdb.duckdb")
    repository.save("unknown", "Unknown", "el-GR", response)

    cached = repository.latest("unknown", "el-GR")

    assert cached is not None
    assert cached.candidates == ()


def test_rejects_naive_cache_timestamp(tmp_path):
    repository = TmdbCandidateRepository(tmp_path / "tmdb.duckdb")
    response = TmdbClient(
        "token",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, request=request, json=tmdb_payload())
        ),
    ).search("title")

    with pytest.raises(ValueError, match="timezone-aware"):
        repository.save("title", "Title", "el-GR", response, datetime(2026, 8, 3, 10))


def test_persists_and_reuses_matched_entity_details(tmp_path):
    response = entity_payload()
    client = TmdbClient(
        "token",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, request=request, json=response)
        ),
    )
    details = client.details("movie", 11, "en-US")
    repository = TmdbEntityRepository(tmp_path / "tmdb.duckdb")
    retrieved_at = datetime(2026, 8, 3, 12, tzinfo=UTC)

    saved = repository.save(details, retrieved_at)
    cached = repository.latest("movie", 11, "en-US")

    assert cached == saved
    assert cached is not None
    assert cached.details.payload == response
    assert repository.latest("movie", 11, "el-GR") is None


def test_records_source_evidence_separately_from_reusable_search_cache(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, json=tmdb_payload())

    repository = TmdbCandidateRepository(tmp_path / "tmdb.duckdb")
    response = TmdbClient("token", transport=httpx.MockTransport(handler)).search("Let it Snow")
    search = repository.save("let it snow", "Let it Snow", "el-GR", response)
    evidence = extract_title_evidence(
        "Χριστουγεννιάτικος Έρωτας στο Καταφύγιο",
        "[Let it Snow] Έτος παραγωγής: 2013 Περιγραφή.",
    )
    created_at = datetime(2026, 8, 3, 11, tzinfo=UTC)

    lookup = repository.record_lookup(
        evidence,
        search.search_id,
        used_query_override=False,
        created_at=created_at,
    )

    assert lookup.source_title == "Χριστουγεννιάτικος Έρωτας στο Καταφύγιο"
    assert lookup.normalized_source_title == "χριστουγεννιατικοσ ερωτασ στο καταφυγιο"
    assert lookup.production_year == 2013
    assert lookup.query_titles == (
        "Let it Snow",
        "Χριστουγεννιάτικος Έρωτας στο Καταφύγιο",
    )
    assert lookup.used_query_override is False
    assert lookup.search_id == search.search_id
    persisted = repository.resolve_lookup(lookup.lookup_id, resolved_at=created_at)

    assert persisted.lookup_id == lookup.lookup_id
    assert persisted.scoring_version == "v1"
    assert persisted.resolution.status.value == "unresolved"
    with duckdb.connect(str(repository.path), read_only=True) as connection:
        row = connection.execute(
            """
            select production_year, search_id
            from tmdb_lookup_contexts
            where lookup_id = ?
            """,
            [lookup.lookup_id],
        ).fetchone()
        score_count = connection.execute(
            "select count(*) from tmdb_candidate_scores where resolution_id = ?",
            [persisted.resolution_id],
        ).fetchone()[0]
        accepted_identity = connection.execute(
            "select tmdb_id, media_type from tmdb_resolutions where resolution_id = ?",
            [persisted.resolution_id],
        ).fetchone()
    assert row == (2013, search.search_id)
    assert score_count == 2
    assert accepted_identity == (None, None)
