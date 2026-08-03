from datetime import UTC, date, datetime

import duckdb

from greek_tv.enrichment import TmdbEntityDetails, TmdbEntityRepository
from greek_tv.enrichment.metric_batch import MetricSnapshotStatus, snapshot_entity_metrics


def entity_details(tmdb_id: int, *, popularity: float = 10.0) -> TmdbEntityDetails:
    return TmdbEntityDetails(
        tmdb_id=tmdb_id,
        media_type="movie",
        language="el-GR",
        title=f"Entity {tmdb_id}",
        original_title=f"Entity {tmdb_id}",
        original_language="en",
        release_date=date(2020, 1, 1),
        overview=None,
        tagline=None,
        runtime_minutes=90,
        status="Released",
        homepage=None,
        imdb_id=None,
        genres=("Drama",),
        production_countries=("US",),
        production_companies=(),
        spoken_languages=("en",),
        popularity=popularity,
        vote_average=7.5,
        vote_count=100,
        payload={
            "id": tmdb_id,
            "popularity": popularity,
            "vote_average": 7.5,
            "vote_count": 100,
        },
    )


class FakeMetricClient:
    def __init__(self, failing_ids: set[int] | None = None) -> None:
        self.failing_ids = failing_ids or set()
        self.requests = []

    def details(self, media_type: str, tmdb_id: int, language: str) -> TmdbEntityDetails:
        self.requests.append((media_type, tmdb_id, language))
        if tmdb_id in self.failing_ids:
            raise RuntimeError("TMDB unavailable")
        return entity_details(tmdb_id, popularity=20.0)


def test_skips_fresh_metrics_without_creating_api_client(tmp_path):
    path = tmp_path / "metrics.duckdb"
    observed_at = datetime(2026, 8, 3, 10, tzinfo=UTC)
    TmdbEntityRepository(path).save(entity_details(11), observed_at)
    client_created = False

    def client_factory():
        nonlocal client_created
        client_created = True
        return FakeMetricClient()

    result = snapshot_entity_metrics(
        path,
        language="el-GR",
        max_age_hours=24,
        client_factory=client_factory,
        clock=lambda: datetime(2026, 8, 3, 12, tzinfo=UTC),
    )

    assert result.count(MetricSnapshotStatus.FRESH) == 1
    assert client_created is False


def test_appends_snapshot_when_metrics_are_stale(tmp_path):
    path = tmp_path / "metrics.duckdb"
    repository = TmdbEntityRepository(path)
    repository.save(entity_details(11), datetime(2026, 8, 1, 10, tzinfo=UTC))
    client = FakeMetricClient()

    result = snapshot_entity_metrics(
        path,
        language="el-GR",
        max_age_hours=24,
        client_factory=lambda: client,
        clock=lambda: datetime(2026, 8, 3, 12, tzinfo=UTC),
    )

    assert result.count(MetricSnapshotStatus.SNAPSHOTTED) == 1
    assert client.requests == [("movie", 11, "el-GR")]
    with duckdb.connect(str(path), read_only=True) as connection:
        rows = connection.execute(
            """
            select popularity, observed_at
            from tmdb_entity_metric_observations
            order by observed_at
            """
        ).fetchall()
    assert rows == [
        (10.0, datetime(2026, 8, 1, 10, tzinfo=UTC)),
        (20.0, datetime(2026, 8, 3, 12, tzinfo=UTC)),
    ]


def test_isolates_metric_snapshot_failures(tmp_path):
    path = tmp_path / "metrics.duckdb"
    repository = TmdbEntityRepository(path)
    old = datetime(2026, 8, 1, 10, tzinfo=UTC)
    repository.save(entity_details(11), old)
    repository.save(entity_details(12), old)
    client = FakeMetricClient({11})

    result = snapshot_entity_metrics(
        path,
        language="el-GR",
        max_age_hours=24,
        client_factory=lambda: client,
        clock=lambda: datetime(2026, 8, 3, 12, tzinfo=UTC),
    )

    assert result.failed == 1
    assert result.count(MetricSnapshotStatus.SNAPSHOTTED) == 1
    assert result.entities[0].error_message == "RuntimeError: TMDB unavailable"
