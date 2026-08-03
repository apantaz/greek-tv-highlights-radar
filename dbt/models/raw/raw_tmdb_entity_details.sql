{{ config(materialized='view', tags=['enrichment']) }}

select
    entity_detail_id,
    tmdb_id,
    media_type,
    language,
    title,
    original_title,
    original_language,
    release_date,
    overview,
    tagline,
    runtime_minutes,
    status,
    homepage,
    imdb_id,
    nullif(json_extract_string(response_json, '$.poster_path'), '') as poster_path,
    genres_json,
    production_countries_json,
    production_companies_json,
    spoken_languages_json,
    retrieved_at,
    response_json
from {{ source('enrichment', 'tmdb_entity_details') }}
