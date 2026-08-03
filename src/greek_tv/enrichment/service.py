"""Reusable orchestration for one evidence-based TMDB enrichment lookup."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from greek_tv.enrichment.evidence import TitleEvidence, extract_title_evidence
from greek_tv.enrichment.repository import (
    CachedTmdbSearch,
    PersistedTmdbResolution,
    TmdbCandidateRepository,
    TmdbLookupContext,
)
from greek_tv.enrichment.titles import normalize_title
from greek_tv.enrichment.tmdb import TmdbClient


class SearchSource(StrEnum):
    CACHED = "cached"
    RETRIEVED = "retrieved"


@dataclass(frozen=True, slots=True)
class EnrichmentOutcome:
    """Persisted search, lookup evidence, and automatic resolution for one title."""

    evidence: TitleEvidence
    search: CachedTmdbSearch
    search_source: SearchSource
    lookup: TmdbLookupContext
    resolution: PersistedTmdbResolution


def enrich_title(
    repository: TmdbCandidateRepository,
    source_title: str,
    description: str | None,
    *,
    language: str,
    client_factory: Callable[[], TmdbClient],
    query_override: str | None = None,
    refresh: bool = False,
) -> EnrichmentOutcome:
    """Retrieve or reuse candidates, persist evidence, and resolve automatically."""
    evidence = extract_title_evidence(source_title, description)
    queries = (
        (normalize_title(query_override).search_title,) if query_override else evidence.query_titles
    )
    search = None
    search_source = SearchSource.CACHED
    client = None
    for query in queries:
        cache_key = normalize_title(query).normalized_title
        search = None if refresh else repository.latest(cache_key, language)
        search_source = SearchSource.CACHED
        if search is None:
            client = client or client_factory()
            response = client.search(query, language)
            search = repository.save(cache_key, query, language, response)
            search_source = SearchSource.RETRIEVED
        if search.candidates:
            break

    if search is None:
        raise RuntimeError("title evidence produced no TMDB queries")
    lookup = repository.record_lookup(
        evidence,
        search.search_id,
        used_query_override=query_override is not None,
    )
    resolution = repository.resolve_lookup(lookup.lookup_id)
    return EnrichmentOutcome(evidence, search, search_source, lookup, resolution)
