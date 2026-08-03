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

{% docs int_tmdb_resolution_id %}Identifier of the selected latest scoring execution.{% enddocs %}
{% docs int_tmdb_lookup_id %}Source-evidence lookup at the model grain.{% enddocs %}
{% docs int_tmdb_scoring_version %}Version of the deterministic scoring policy used.{% enddocs %}
{% docs int_tmdb_resolution_status %}Latest outcome: matched, unresolved, or null while pending.{% enddocs %}
{% docs int_tmdb_resolution_reason %}Machine-readable explanation for the latest outcome.{% enddocs %}
{% docs int_tmdb_winning_candidate_rank %}Original response rank of the highest-scoring candidate.{% enddocs %}
{% docs int_tmdb_id %}Accepted TMDB ID interpreted with media type; null unless matched.{% enddocs %}
{% docs int_tmdb_media_type %}Accepted TMDB entity type; movie or television.{% enddocs %}
{% docs int_tmdb_winning_score %}Total confidence score of the winning candidate.{% enddocs %}
{% docs int_tmdb_runner_up_score %}Total confidence score of the runner-up candidate.{% enddocs %}
{% docs int_tmdb_score_margin %}Difference between winning and runner-up confidence.{% enddocs %}
{% docs int_tmdb_resolved_at %}UTC timestamp of the selected scoring execution.{% enddocs %}
{% docs int_tmdb_entity_detail_id %}Identifier of the selected localized entity-details response.{% enddocs %}
{% docs int_tmdb_language %}TMDB response language used for lookup and entity details.{% enddocs %}
{% docs int_tmdb_entity_title %}Latest localized TMDB entity title.{% enddocs %}
{% docs int_tmdb_original_title %}TMDB entity title in its original language.{% enddocs %}
{% docs int_tmdb_original_language %}ISO code for the entity's original language.{% enddocs %}
{% docs int_tmdb_release_date %}Movie release date or television first-air date.{% enddocs %}
{% docs int_tmdb_overview %}Latest localized entity synopsis when available.{% enddocs %}
{% docs int_tmdb_tagline %}Latest localized entity tagline when available.{% enddocs %}
{% docs int_tmdb_runtime_minutes %}Movie runtime or first stated television episode runtime.{% enddocs %}
{% docs int_tmdb_entity_status %}Latest production or release status supplied by TMDB.{% enddocs %}
{% docs int_tmdb_homepage %}Official entity homepage when available.{% enddocs %}
{% docs int_tmdb_imdb_id %}IMDb identifier supplied directly by TMDB when available.{% enddocs %}
{% docs int_tmdb_genres_json %}Ordered latest genre names serialized as JSON.{% enddocs %}
{% docs int_tmdb_production_countries_json %}Ordered ISO production-country codes serialized as JSON.{% enddocs %}
{% docs int_tmdb_production_companies_json %}Ordered production-company names serialized as JSON.{% enddocs %}
{% docs int_tmdb_spoken_languages_json %}Ordered ISO spoken-language codes serialized as JSON.{% enddocs %}
{% docs int_tmdb_entity_retrieved_at %}UTC timestamp of the selected entity-details retrieval.{% enddocs %}
{% docs int_tmdb_response_json %}Complete selected raw TMDB details response.{% enddocs %}
{% docs int_tmdb_metric_observation_id %}Identifier of the selected latest metric observation.{% enddocs %}
{% docs int_tmdb_popularity %}Latest observed TMDB popularity value.{% enddocs %}
{% docs int_tmdb_vote_average %}Latest observed TMDB average vote value.{% enddocs %}
{% docs int_tmdb_vote_count %}Latest observed TMDB vote count.{% enddocs %}
{% docs int_tmdb_metrics_observed_at %}UTC timestamp of the selected metric observation.{% enddocs %}
{% docs int_tmdb_source_title %}Complete programme title preserved from the schedule.{% enddocs %}
{% docs int_tmdb_normalized_source_title %}Canonical source-title identity used for comparison.{% enddocs %}
{% docs int_tmdb_production_year %}Production year explicitly extracted from source text.{% enddocs %}
{% docs int_tmdb_query_titles_json %}Ordered source-derived search variants serialized as JSON.{% enddocs %}
{% docs int_tmdb_used_query_override %}Whether a diagnostic override selected the cached search.{% enddocs %}
{% docs int_tmdb_search_id %}Cached TMDB search selected for this lookup.{% enddocs %}
{% docs int_tmdb_search_query %}Human-readable query sent for the selected TMDB search.{% enddocs %}
{% docs int_tmdb_lookup_created_at %}UTC timestamp at which source evidence was recorded.{% enddocs %}
{% docs int_enrichment_observation_id %}Current schedule observation at the model grain.{% enddocs %}
{% docs int_enrichment_linked_at %}UTC timestamp of the selected direct enrichment link.{% enddocs %}
