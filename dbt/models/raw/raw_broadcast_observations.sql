select
    observation_id,
    run_id,
    broadcast_id,
    channel,
    title,
    starts_at,
    ends_at,
    description,
    source_url,
    retrieved_at
from {{ source('ingestion', 'broadcast_observations') }}
