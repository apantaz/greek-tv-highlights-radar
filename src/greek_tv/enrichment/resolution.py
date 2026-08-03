"""Conservative, explainable, and fully automatic TMDB entity resolution."""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from difflib import SequenceMatcher
from enum import StrEnum

from greek_tv.enrichment.titles import normalize_title
from greek_tv.enrichment.tmdb import TmdbCandidate

ACCEPTANCE_THRESHOLD = 85.0
MINIMUM_WINNER_MARGIN = 10.0
TITLE_WEIGHT_WITH_YEAR = 0.75
YEAR_WEIGHT = 0.25


class ResolutionStatus(StrEnum):
    MATCHED = "matched"
    UNRESOLVED = "unresolved"


class ResolutionReason(StrEnum):
    ACCEPTED = "accepted"
    NO_CANDIDATES = "no_candidates"
    BELOW_THRESHOLD = "below_threshold"
    AMBIGUOUS_CANDIDATES = "ambiguous_candidates"


@dataclass(frozen=True, slots=True)
class CandidateScore:
    """Auditable score components for one TMDB candidate."""

    candidate: TmdbCandidate
    title_score: float
    year_score: float | None
    total_score: float
    score_rank: int


@dataclass(frozen=True, slots=True)
class Resolution:
    """A conservative match or an explicit unresolved outcome."""

    status: ResolutionStatus
    reason: ResolutionReason
    scores: tuple[CandidateScore, ...]
    winner: CandidateScore | None
    runner_up_score: float | None
    score_margin: float | None


def resolve_candidates(
    search_query: str,
    production_year: int | None,
    candidates: tuple[TmdbCandidate, ...],
) -> Resolution:
    """Rank candidates and accept only a strong winner with a safe score margin."""
    ranked = _score_candidates(search_query, production_year, candidates)
    if not ranked:
        return Resolution(
            ResolutionStatus.UNRESOLVED,
            ResolutionReason.NO_CANDIDATES,
            (),
            None,
            None,
            None,
        )

    winner = ranked[0]
    runner_up_score = ranked[1].total_score if len(ranked) > 1 else None
    score_margin = (
        round(winner.total_score - runner_up_score, 2)
        if runner_up_score is not None
        else winner.total_score
    )
    if winner.total_score < ACCEPTANCE_THRESHOLD:
        status = ResolutionStatus.UNRESOLVED
        reason = ResolutionReason.BELOW_THRESHOLD
    elif len(ranked) > 1 and score_margin < MINIMUM_WINNER_MARGIN:
        status = ResolutionStatus.UNRESOLVED
        reason = ResolutionReason.AMBIGUOUS_CANDIDATES
    else:
        status = ResolutionStatus.MATCHED
        reason = ResolutionReason.ACCEPTED

    return Resolution(status, reason, ranked, winner, runner_up_score, score_margin)


def _score_candidates(
    search_query: str,
    production_year: int | None,
    candidates: tuple[TmdbCandidate, ...],
) -> tuple[CandidateScore, ...]:
    provisional = []
    for candidate in candidates:
        title_score = _title_score(search_query, candidate)
        year_score = _year_score(production_year, candidate.release_date)
        total_score = (
            title_score
            if year_score is None
            else title_score * TITLE_WEIGHT_WITH_YEAR + year_score * YEAR_WEIGHT
        )
        provisional.append((candidate, title_score, year_score, round(total_score, 2)))

    provisional.sort(key=lambda item: (-item[3], item[0].rank, item[0].tmdb_id))
    return tuple(
        CandidateScore(candidate, title_score, year_score, total_score, rank)
        for rank, (candidate, title_score, year_score, total_score) in enumerate(
            provisional, start=1
        )
    )


def _title_score(search_query: str, candidate: TmdbCandidate) -> float:
    query = normalize_title(search_query).normalized_title
    titles = {
        normalize_title(candidate.title).normalized_title,
        normalize_title(candidate.original_title).normalized_title,
    }
    return round(max(SequenceMatcher(None, query, title).ratio() for title in titles) * 100, 2)


def _year_score(production_year: int | None, release_date: date | None) -> float | None:
    if production_year is None:
        return None
    if release_date is None:
        return 0.0
    difference = abs(production_year - release_date.year)
    return {0: 100.0, 1: 60.0, 2: 30.0}.get(difference, 0.0)


def resolution_timestamp(value: datetime | None = None) -> datetime:
    """Return a timezone-aware scoring timestamp."""
    value = value or datetime.now(UTC)
    if value.tzinfo is None:
        raise ValueError("resolution timestamp must be timezone-aware")
    return value
