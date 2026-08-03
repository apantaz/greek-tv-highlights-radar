{{ config(materialized='view', tags=['enrichment']) }}

select
    resolution_id,
    lookup_id,
    scoring_version,
    status,
    reason,
    winning_candidate_rank,
    tmdb_id,
    media_type,
    winning_score,
    runner_up_score,
    score_margin,
    resolved_at
from {{ source('enrichment', 'tmdb_resolutions') }}
