{{ config(materialized='view') }}

with successful_runs as (
    select
        run_id,
        source,
        channel,
        schedule_date,
        source_url,
        started_at,
        completed_at,
        status,
        records_parsed,
        snapshot_path,
        row_number() over (
            partition by source, channel, schedule_date
            order by completed_at desc, started_at desc, run_id desc
        ) as run_recency
    from {{ ref('raw_ingestion_runs') }}
    where true
        and status = 'succeeded'
)

select
    run_id,
    source,
    channel,
    schedule_date,
    source_url,
    started_at,
    completed_at,
    status,
    records_parsed,
    snapshot_path
from successful_runs
where true
    and run_recency = 1
