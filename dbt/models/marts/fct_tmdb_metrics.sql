{{ config(materialized='table', tags=['fact', 'enrichment']) }}

select
    metrics.metric_observation_id,
    metrics.entity_detail_id,
    programmes.programme_key,
    metrics.tmdb_id,
    metrics.media_type,
    metrics.popularity,
    metrics.vote_average,
    metrics.vote_count,
    metrics.observed_at,
    cast(timezone('UTC', metrics.observed_at) as date) as observation_date
from {{ ref('raw_tmdb_entity_metric_observations') }} as metrics
inner join {{ ref('dim_programmes') }} as programmes
    on metrics.media_type = programmes.media_type
    and metrics.tmdb_id = programmes.tmdb_id
