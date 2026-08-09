{{ config(materialized='view', tags=['enrichment']) }}

with ranked_details as (
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
        poster_path,
        genres_json,
        production_countries_json,
        production_companies_json,
        spoken_languages_json,
        retrieved_at,
        response_json,
        row_number() over (
            partition by media_type, tmdb_id, language
            order by retrieved_at desc, entity_detail_id desc
        ) as detail_recency
    from {{ ref('raw_tmdb_entity_details') }}
)

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
    poster_path,
    genres_json,
    production_countries_json,
    production_companies_json,
    spoken_languages_json,
    retrieved_at,
    response_json
from ranked_details
where detail_recency = 1
