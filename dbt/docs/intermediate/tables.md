{% docs int_latest_successful_ingestion_runs %}

# Latest successful ingestion runs

One latest successful ingestion run per source, channel, and requested schedule date.
Runs are selected deterministically by completion time, start time, and run identifier
so downstream schedules never depend on database row order.

{% enddocs %}

{% docs int_current_broadcasts %}

# Current broadcasts

Programme observations belonging to the latest successful ingestion run for each
source, channel, and requested schedule date. The model excludes failed attempts and
superseded successful observations while preserving their complete history upstream.

{% enddocs %}
