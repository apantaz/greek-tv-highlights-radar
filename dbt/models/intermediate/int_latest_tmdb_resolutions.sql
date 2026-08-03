{{ config(materialized='view', tags=['enrichment']) }}

with ranked_resolutions as (
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
        resolved_at,
        row_number() over (
            partition by lookup_id
            order by resolved_at desc, resolution_id desc
        ) as resolution_recency
    from {{ ref('raw_tmdb_resolutions') }}
)

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
from ranked_resolutions
where resolution_recency = 1
