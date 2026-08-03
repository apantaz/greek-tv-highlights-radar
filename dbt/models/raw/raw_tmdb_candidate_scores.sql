{{ config(materialized='view', tags=['enrichment']) }}

select
    resolution_id,
    candidate_rank,
    tmdb_id,
    title_score,
    year_score,
    total_score,
    score_rank
from {{ source('enrichment', 'tmdb_candidate_scores') }}
