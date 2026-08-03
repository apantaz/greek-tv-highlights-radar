{{ config(materialized='view', tags=['enrichment']) }}

select
    lookup_id,
    source_title,
    normalized_source_title,
    production_year,
    query_titles_json,
    used_query_override,
    search_id,
    created_at
from {{ source('enrichment', 'tmdb_lookup_contexts') }}
