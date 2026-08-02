{% docs raw_ingestion_runs_run_id %}
Unique identifier assigned before ingestion work begins.
{% enddocs %}

{% docs raw_ingestion_runs_source %}
Upstream schedule source identifier.
{% enddocs %}

{% docs raw_ingestion_runs_channel %}
Channel display name observed during catalog discovery.
{% enddocs %}

{% docs raw_ingestion_runs_schedule_date %}
Calendar date requested from the source.
{% enddocs %}

{% docs raw_ingestion_runs_source_url %}
Date-addressable upstream schedule URL.
{% enddocs %}

{% docs raw_ingestion_runs_started_at %}
UTC timestamp at which the ingestion attempt began.
{% enddocs %}

{% docs raw_ingestion_runs_completed_at %}
UTC timestamp at which the attempt succeeded or failed.
{% enddocs %}

{% docs raw_ingestion_runs_status %}
Run state recorded as running, succeeded, or failed.
{% enddocs %}

{% docs raw_ingestion_runs_records_parsed %}
Number of observations persisted by a successful run.
{% enddocs %}

{% docs raw_ingestion_runs_snapshot_path %}
Local path to the immutable raw HTML response, when available.
{% enddocs %}

{% docs raw_ingestion_runs_error_message %}
Bounded diagnostic message recorded for a failed run.
{% enddocs %}

{% docs raw_broadcast_observations_observation_id %}
Stable identifier for a broadcast within an ingestion run.
{% enddocs %}

{% docs raw_broadcast_observations_run_id %}
Ingestion run that produced this observation.
{% enddocs %}

{% docs raw_broadcast_observations_broadcast_id %}
Source-observation identity derived from schedule attributes.
{% enddocs %}

{% docs raw_broadcast_observations_channel %}
Channel display name associated with the programme.
{% enddocs %}

{% docs raw_broadcast_observations_title %}
Programme title as observed in the source schedule.
{% enddocs %}

{% docs raw_broadcast_observations_starts_at %}
Timezone-aware scheduled start timestamp.
{% enddocs %}

{% docs raw_broadcast_observations_ends_at %}
Derived scheduled end timestamp, when another programme follows.
{% enddocs %}

{% docs raw_broadcast_observations_description %}
Optional programme description supplied by the source.
{% enddocs %}

{% docs raw_broadcast_observations_source_url %}
Upstream page from which the observation was parsed.
{% enddocs %}

{% docs raw_broadcast_observations_retrieved_at %}
UTC timestamp at which the source response was retrieved.
{% enddocs %}
