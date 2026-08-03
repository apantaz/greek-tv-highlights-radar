{{ config(materialized='view') }}

select
    observations.observation_id,
    observations.broadcast_id,
    observations.run_id,
    runs.source,
    observations.channel,
    runs.schedule_date,
    observations.title,
    observations.starts_at,
    observations.ends_at,
    observations.description,
    observations.source_url,
    observations.retrieved_at,
    runs.completed_at as ingestion_completed_at
from {{ ref('raw_broadcast_observations') }} as observations
inner join {{ ref('int_latest_successful_ingestion_runs') }} as runs
    on observations.run_id = runs.run_id
