{{ config(materialized='table', tags=['dimension', 'enrichment']) }}

with ranked_metadata as (
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
        row_number() over (
            partition by media_type, tmdb_id
            order by
                case when language = 'el-GR' then 0 else 1 end,
                retrieved_at desc,
                language,
                entity_detail_id desc
        ) as metadata_preference
    from {{ ref('int_latest_tmdb_entity_details') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['media_type', 'tmdb_id']) }} as programme_key,
    entity_detail_id,
    tmdb_id,
    media_type,
    language as metadata_language,
    title,
    original_title,
    original_language,
    release_date,
    extract(year from release_date)::integer as release_year,
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
    retrieved_at as metadata_retrieved_at
from ranked_metadata
where metadata_preference = 1
