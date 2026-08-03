{{ config(materialized='view', tags=['enrichment']) }}

with ranked_links as (
    select
        observation_id,
        lookup_id,
        language,
        scoring_version,
        linked_at,
        row_number() over (
            partition by observation_id
            order by linked_at desc, lookup_id desc
        ) as link_recency
    from {{ ref('raw_broadcast_enrichment_lookups') }}
),

latest_links as (
    select
        observation_id,
        lookup_id,
        language,
        scoring_version,
        linked_at
    from ranked_links
    where link_recency = 1
)

select
    broadcasts.observation_id,
    links.lookup_id,
    links.language,
    links.scoring_version,
    links.linked_at,
    programmes.resolution_id,
    programmes.resolution_status,
    programmes.resolution_reason,
    programmes.tmdb_id,
    programmes.media_type,
    programmes.entity_detail_id,
    programmes.metric_observation_id
from {{ ref('int_current_broadcasts') }} as broadcasts
left join latest_links as links
    on broadcasts.observation_id = links.observation_id
left join {{ ref('int_resolved_programmes') }} as programmes
    on links.lookup_id = programmes.lookup_id
