{{ config(materialized='table', tags=['aggregate']) }}

select
    channel_key,
    source,
    channel,
    schedule_date,
    count(*) as programme_count,
    count(duration_minutes) as programmes_with_known_duration,
    sum(coalesce(duration_minutes, 0)) as known_scheduled_minutes,
    min(starts_at_local) as first_programme_starts_at_local,
    max(ends_at_local) as last_programme_ends_at_local,
    count(*) filter (where crosses_midnight) as programmes_crossing_midnight,
    max(ingestion_completed_at) as ingestion_completed_at
from {{ ref('fct_current_broadcasts') }}
group by
    channel_key,
    source,
    channel,
    schedule_date
