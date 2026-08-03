{{ config(materialized='view', tags=['enrichment']) }}

select
    search_id,
    normalized_title,
    search_query,
    language,
    retrieved_at,
    response_json
from {{ source('enrichment', 'tmdb_searches') }}
