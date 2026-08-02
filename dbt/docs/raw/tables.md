{% docs raw_ingestion_runs %}

# Raw ingestion runs

Typed, analysis-ready projection of immutable ingestion attempts. The model preserves
the source grain of one row per attempted source, channel, and schedule date
ingestion.

{% enddocs %}

{% docs raw_broadcast_observations %}

# Raw broadcast observations

Typed, analysis-ready projection of programme observations. The model preserves the
source grain of one programme row observed during one successful ingestion run.

{% enddocs %}
