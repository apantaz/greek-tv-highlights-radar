{{ config(materialized='table', tags=['fact']) }}

with broadcasts as (
    select
        observation_id,
        broadcast_id,
        run_id,
        source,
        channel,
        schedule_date,
        title,
        starts_at,
        ends_at,
        timezone('Europe/Athens', starts_at) as starts_at_local,
        timezone('Europe/Athens', ends_at) as ends_at_local,
        description,
        source_url,
        retrieved_at,
        ingestion_completed_at
    from {{ ref('int_current_broadcasts') }}
),

enriched as (
    select
        observation_id,
        broadcast_id,
        run_id,
        source,
        channel,
        schedule_date,
        cast(starts_at_local as date) as broadcast_date,
        title,
        starts_at,
        ends_at,
        starts_at_local,
        ends_at_local,
        case
            when ends_at is not null then date_diff('minute', starts_at, ends_at)
        end as duration_minutes,
        case
            when ends_at_local is null then false
            else cast(starts_at_local as date) <> cast(ends_at_local as date)
        end as crosses_midnight,
        row_number() over (
            partition by source, channel, schedule_date
            order by starts_at, observation_id
        ) as programme_position,
        description,
        source_url,
        retrieved_at,
        ingestion_completed_at
    from broadcasts
)

select
    enriched.observation_id,
    enriched.broadcast_id,
    enriched.run_id,
    channels.channel_key,
    programmes.programme_key,
    enrichment.lookup_id,
    enrichment.resolution_id,
    enrichment.resolution_status,
    enrichment.tmdb_id,
    enrichment.media_type,
    enriched.source,
    enriched.channel,
    enriched.schedule_date,
    enriched.broadcast_date,
    enriched.title,
    enriched.starts_at,
    enriched.ends_at,
    enriched.starts_at_local,
    enriched.ends_at_local,
    enriched.duration_minutes,
    enriched.crosses_midnight,
    enriched.programme_position,
    enriched.description,
    enriched.source_url,
    enriched.retrieved_at,
    enriched.ingestion_completed_at
from enriched
inner join {{ ref('dim_channels') }} as channels
    on enriched.source = channels.source
    and enriched.channel = channels.channel
left join {{ ref('int_current_broadcast_enrichment') }} as enrichment
    on enriched.observation_id = enrichment.observation_id
left join {{ ref('dim_programmes') }} as programmes
    on enrichment.media_type = programmes.media_type
    and enrichment.tmdb_id = programmes.tmdb_id
