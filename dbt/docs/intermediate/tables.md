{% docs int_latest_successful_ingestion_runs %}

# Latest successful ingestion runs

One latest successful ingestion run per source, channel, and requested schedule date.
Runs are selected deterministically by completion time, start time, and run identifier
so downstream schedules never depend on database row order.

{% enddocs %}

{% docs int_latest_tmdb_resolutions %}

# Latest TMDB resolutions

One deterministic latest scoring execution per source-evidence lookup. The model
preserves matched and unresolved outcomes while hiding superseded scoring runs.

{% enddocs %}

{% docs int_latest_tmdb_entity_details %}

# Latest TMDB entity details

One latest full-detail response per TMDB media type, entity ID, and response language.
Retrieval timestamp and identifier provide deterministic tie-breaking.

{% enddocs %}

{% docs int_latest_tmdb_entity_metrics %}

# Latest TMDB entity metrics

One latest popularity and voting observation per TMDB media type and entity ID. Full
metric history remains available in the raw model.

{% enddocs %}

{% docs int_resolved_programmes %}

# Resolved programmes

One row per source-evidence lookup combining its latest resolution with compatible
localized entity details and latest metrics. Pending and unresolved lookups remain in
the model with null accepted identity and metadata fields.

{% enddocs %}

{% docs int_current_broadcasts %}

# Current broadcasts

Programme observations belonging to the latest successful ingestion run for each
source, channel, and requested schedule date. The model excludes failed attempts and
superseded successful observations while preserving their complete history upstream.

{% enddocs %}
