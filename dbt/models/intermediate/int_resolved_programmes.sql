{{ config(materialized='view', tags=['enrichment']) }}

select
    contexts.lookup_id,
    contexts.source_title,
    contexts.normalized_source_title,
    contexts.production_year,
    contexts.query_titles_json,
    contexts.used_query_override,
    contexts.search_id,
    searches.search_query,
    searches.language,
    contexts.created_at as lookup_created_at,
    resolutions.resolution_id,
    resolutions.scoring_version,
    resolutions.status as resolution_status,
    resolutions.reason as resolution_reason,
    resolutions.winning_candidate_rank,
    resolutions.tmdb_id,
    resolutions.media_type,
    resolutions.winning_score,
    resolutions.runner_up_score,
    resolutions.score_margin,
    resolutions.resolved_at,
    details.entity_detail_id,
    details.title as entity_title,
    details.original_title,
    details.original_language,
    details.release_date,
    details.overview,
    details.tagline,
    details.runtime_minutes,
    details.status as entity_status,
    details.homepage,
    details.imdb_id,
    details.genres_json,
    details.production_countries_json,
    details.production_companies_json,
    details.spoken_languages_json,
    details.retrieved_at as entity_retrieved_at,
    metrics.metric_observation_id,
    metrics.popularity,
    metrics.vote_average,
    metrics.vote_count,
    metrics.observed_at as metrics_observed_at
from {{ ref('raw_tmdb_lookup_contexts') }} as contexts
inner join {{ ref('raw_tmdb_searches') }} as searches
    on contexts.search_id = searches.search_id
left join {{ ref('int_latest_tmdb_resolutions') }} as resolutions
    on contexts.lookup_id = resolutions.lookup_id
left join {{ ref('int_latest_tmdb_entity_details') }} as details
    on resolutions.media_type = details.media_type
    and resolutions.tmdb_id = details.tmdb_id
    and searches.language = details.language
left join {{ ref('int_latest_tmdb_entity_metrics') }} as metrics
    on resolutions.media_type = metrics.media_type
    and resolutions.tmdb_id = metrics.tmdb_id
