{{ config(materialized='view', tags=['enrichment']) }}

with ranked_metrics as (
    select
        metric_observation_id,
        entity_detail_id,
        tmdb_id,
        media_type,
        popularity,
        vote_average,
        vote_count,
        observed_at,
        row_number() over (
            partition by media_type, tmdb_id
            order by observed_at desc, metric_observation_id desc
        ) as metric_recency
    from {{ ref('raw_tmdb_entity_metric_observations') }}
)

select
    metric_observation_id,
    entity_detail_id,
    tmdb_id,
    media_type,
    popularity,
    vote_average,
    vote_count,
    observed_at
from ranked_metrics
where metric_recency = 1
