{{ config(materialized='view', tags=['enrichment']) }}

select
    search_id,
    candidate_rank,
    tmdb_id,
    media_type,
    title,
    original_title,
    original_language,
    release_date,
    overview,
    popularity,
    vote_average,
    vote_count
from {{ source('enrichment', 'tmdb_candidates') }}
