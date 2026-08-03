{{ config(materialized='table') }}

select
    {{ dbt_utils.generate_surrogate_key(['source', 'channel']) }} as channel_key,
    source,
    channel,
    min(schedule_date) as first_schedule_date,
    max(schedule_date) as latest_schedule_date,
    min(retrieved_at) as first_observed_at,
    max(retrieved_at) as latest_observed_at
from {{ ref('int_current_broadcasts') }}
group by source, channel
