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
    error_message
from {{ source('ingestion', 'ingestion_runs') }}
