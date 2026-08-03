from datetime import date, datetime

import pytest

from greek_tv.enrichment import (
    ResolutionReason,
    ResolutionStatus,
    TmdbCandidate,
    resolve_candidates,
)


def candidate(
    rank: int,
    tmdb_id: int,
    title: str,
    year: int | None,
    media_type: str = "movie",
) -> TmdbCandidate:
    return TmdbCandidate(
        rank=rank,
        tmdb_id=tmdb_id,
        media_type=media_type,
        title=title,
        original_title=title,
        original_language="en",
        release_date=date(year, 1, 1) if year else None,
        overview=None,
        popularity=None,
        vote_average=None,
        vote_count=None,
    )


def test_accepts_exact_title_and_year_with_clear_margin():
    resolution = resolve_candidates(
        "Let it Snow",
        2013,
        (
            candidate(1, 1, "Let It Snow", 2020),
            candidate(2, 2, "Let It Snow", 2013),
            candidate(3, 3, "Snow Day", 2013),
        ),
    )

    assert resolution.status is ResolutionStatus.MATCHED
    assert resolution.reason is ResolutionReason.ACCEPTED
    assert resolution.winner is not None
    assert resolution.winner.candidate.tmdb_id == 2
    assert resolution.winner.title_score == 100
    assert resolution.winner.year_score == 100
    assert resolution.winner.total_score == 100
    assert resolution.score_margin == 25


def test_leaves_tied_strong_candidates_unresolved():
    resolution = resolve_candidates(
        "Shared Title",
        2020,
        (
            candidate(1, 1, "Shared Title", 2020, "movie"),
            candidate(2, 2, "Shared Title", 2020, "tv"),
        ),
    )

    assert resolution.status is ResolutionStatus.UNRESOLVED
    assert resolution.reason is ResolutionReason.AMBIGUOUS_CANDIDATES
    assert resolution.score_margin == 0


def test_leaves_weak_best_candidate_unresolved():
    resolution = resolve_candidates(
        "Completely Different",
        2013,
        (candidate(1, 1, "Unrelated Programme", 2013),),
    )

    assert resolution.status is ResolutionStatus.UNRESOLVED
    assert resolution.reason is ResolutionReason.BELOW_THRESHOLD


def test_accepts_unique_exact_title_when_source_year_is_unavailable():
    resolution = resolve_candidates(
        "Unique Programme",
        None,
        (
            candidate(1, 1, "Unique Programme", 2020),
            candidate(2, 2, "Different Programme", 2020),
        ),
    )

    assert resolution.status is ResolutionStatus.MATCHED
    assert resolution.winner is not None
    assert resolution.winner.year_score is None
    assert resolution.winner.total_score == 100


def test_records_explicit_no_candidates_outcome():
    resolution = resolve_candidates("Missing", 2020, ())

    assert resolution.status is ResolutionStatus.UNRESOLVED
    assert resolution.reason is ResolutionReason.NO_CANDIDATES
    assert resolution.winner is None


def test_rejects_naive_resolution_timestamp():
    from greek_tv.enrichment.resolution import resolution_timestamp

    with pytest.raises(ValueError, match="timezone-aware"):
        resolution_timestamp(datetime(2026, 8, 3, 10))
