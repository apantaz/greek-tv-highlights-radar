"""Programme metadata enrichment and entity-resolution helpers."""

from greek_tv.enrichment.evidence import TitleEvidence, extract_title_evidence
from greek_tv.enrichment.repository import (
    CachedTmdbSearch,
    TmdbCandidateRepository,
    TmdbLookupContext,
)
from greek_tv.enrichment.titles import NormalizedTitle, normalize_title
from greek_tv.enrichment.tmdb import TmdbCandidate, TmdbClient, TmdbSearchResponse

__all__ = [
    "CachedTmdbSearch",
    "NormalizedTitle",
    "TitleEvidence",
    "TmdbCandidate",
    "TmdbCandidateRepository",
    "TmdbClient",
    "TmdbLookupContext",
    "TmdbSearchResponse",
    "extract_title_evidence",
    "normalize_title",
]
