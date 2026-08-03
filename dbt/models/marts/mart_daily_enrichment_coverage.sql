{{ config(materialized='table', tags=['aggregate', 'enrichment']) }}

select
    channel_key,
    source,
    channel,
    schedule_date,
    count(*) as programme_count,
    count(lookup_id) as submitted_for_enrichment,
    count(resolution_id) as resolved_programmes,
    count(*) filter (where resolution_status = 'matched') as matched_programmes,
    count(*) filter (where resolution_status = 'unresolved') as unresolved_programmes,
    count(programme_key) as programmes_with_canonical_metadata,
    count(*) filter (where lookup_id is null) as programmes_missing_enrichment,
    count(*) filter (
        where resolution_status = 'matched' and programme_key is null
    ) as matched_programmes_missing_metadata,
    round(100.0 * count(lookup_id) / count(*), 2) as enrichment_coverage_pct,
    round(100.0 * count(resolution_id) / count(*), 2) as resolution_coverage_pct,
    round(
        100.0
        * count(*) filter (where resolution_status = 'matched')
        / nullif(count(resolution_id), 0),
        2
    ) as match_rate_pct,
    round(100.0 * count(programme_key) / count(*), 2) as canonical_metadata_coverage_pct,
    max(ingestion_completed_at) as ingestion_completed_at
from {{ ref('fct_current_broadcasts') }}
group by
    channel_key,
    source,
    channel,
    schedule_date
