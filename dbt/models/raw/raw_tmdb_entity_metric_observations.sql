{{ config(materialized='view', tags=['enrichment']) }}

select
    metric_observation_id,
    entity_detail_id,
    tmdb_id,
    media_type,
    popularity,
    vote_average,
    vote_count,
    observed_at
from {{ source('enrichment', 'tmdb_entity_metric_observations') }}
