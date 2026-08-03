{% docs int_latest_successful_ingestion_runs_run_id %}
Identifier of the selected latest successful ingestion run.
{% enddocs %}

{% docs int_latest_successful_ingestion_runs_source %}
Upstream schedule source used to partition run recency.
{% enddocs %}

{% docs int_latest_successful_ingestion_runs_channel %}
Channel used to partition run recency.
{% enddocs %}

{% docs int_latest_successful_ingestion_runs_schedule_date %}
Requested schedule date used to partition run recency.
{% enddocs %}

{% docs int_latest_successful_ingestion_runs_source_url %}
Date-addressable upstream schedule URL used by the selected run.
{% enddocs %}

{% docs int_latest_successful_ingestion_runs_started_at %}
UTC timestamp at which the selected run began.
{% enddocs %}

{% docs int_latest_successful_ingestion_runs_completed_at %}
UTC timestamp at which the selected run completed successfully.
{% enddocs %}

{% docs int_latest_successful_ingestion_runs_status %}
Run status, constrained to succeeded in this model.
{% enddocs %}

{% docs int_latest_successful_ingestion_runs_records_parsed %}
Number of observations persisted by the selected successful run.
{% enddocs %}

{% docs int_latest_successful_ingestion_runs_snapshot_path %}
Local path to the immutable raw HTML response for the selected run.
{% enddocs %}

{% docs int_current_broadcasts_observation_id %}
Stable identifier for the programme observation within its ingestion run.
{% enddocs %}

{% docs int_current_broadcasts_broadcast_id %}
Source-observation identity derived from schedule attributes.
{% enddocs %}

{% docs int_current_broadcasts_run_id %}
Latest successful ingestion run that produced the observation.
{% enddocs %}

{% docs int_current_broadcasts_source %}
Upstream schedule source inherited from the selected ingestion run.
{% enddocs %}

{% docs int_current_broadcasts_channel %}
Channel associated with the programme observation.
{% enddocs %}

{% docs int_current_broadcasts_schedule_date %}
Schedule date requested by the selected ingestion run.
{% enddocs %}

{% docs int_current_broadcasts_title %}
Programme title observed in the current source schedule.
{% enddocs %}

{% docs int_current_broadcasts_starts_at %}
Timezone-aware scheduled programme start timestamp.
{% enddocs %}

{% docs int_current_broadcasts_ends_at %}
Derived scheduled end timestamp, when another programme follows.
{% enddocs %}

{% docs int_current_broadcasts_description %}
Optional programme description supplied by the source.
{% enddocs %}

{% docs int_current_broadcasts_source_url %}
Upstream page from which the programme observation was parsed.
{% enddocs %}

{% docs int_current_broadcasts_retrieved_at %}
UTC timestamp at which the programme source response was retrieved.
{% enddocs %}

{% docs int_current_broadcasts_ingestion_completed_at %}
UTC timestamp at which the selected ingestion run completed successfully.
{% enddocs %}
