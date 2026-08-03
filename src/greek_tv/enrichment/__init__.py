"""Programme metadata enrichment and entity-resolution helpers."""

from greek_tv.enrichment.entities import (
    CachedTmdbEntity,
    TmdbEntityRepository,
    TmdbMetricObservation,
)
from greek_tv.enrichment.entity_batch import (
    BatchEntityEnrichmentResult,
    EntityEnrichmentResult,
    EntityEnrichmentStatus,
    enrich_matched_entities,
)
from greek_tv.enrichment.evidence import TitleEvidence, extract_title_evidence
from greek_tv.enrichment.metric_batch import (
    BatchMetricSnapshotResult,
    MetricSnapshotResult,
    MetricSnapshotStatus,
    snapshot_entity_metrics,
)
from greek_tv.enrichment.repository import (
    CachedTmdbSearch,
    PersistedTmdbResolution,
    TmdbCandidateRepository,
    TmdbLookupContext,
)
from greek_tv.enrichment.resolution import (
    CandidateScore,
    Resolution,
    ResolutionReason,
    ResolutionStatus,
    resolve_candidates,
)
from greek_tv.enrichment.titles import NormalizedTitle, normalize_title
from greek_tv.enrichment.tmdb import (
    TmdbCandidate,
    TmdbClient,
    TmdbEntityDetails,
    TmdbSearchResponse,
)

__all__ = [
    "BatchEntityEnrichmentResult",
    "BatchMetricSnapshotResult",
    "CachedTmdbEntity",
    "CachedTmdbSearch",
    "CandidateScore",
    "EntityEnrichmentResult",
    "EntityEnrichmentStatus",
    "MetricSnapshotResult",
    "MetricSnapshotStatus",
    "NormalizedTitle",
    "PersistedTmdbResolution",
    "Resolution",
    "ResolutionReason",
    "ResolutionStatus",
    "TitleEvidence",
    "TmdbCandidate",
    "TmdbCandidateRepository",
    "TmdbClient",
    "TmdbEntityDetails",
    "TmdbEntityRepository",
    "TmdbLookupContext",
    "TmdbMetricObservation",
    "TmdbSearchResponse",
    "enrich_matched_entities",
    "extract_title_evidence",
    "normalize_title",
    "resolve_candidates",
    "snapshot_entity_metrics",
]
