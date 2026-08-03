{{ config(materialized='view', tags=['enrichment']) }}

select
    observation_id,
    lookup_id,
    language,
    scoring_version,
    linked_at
from {{ source('enrichment', 'broadcast_enrichment_lookups') }}
