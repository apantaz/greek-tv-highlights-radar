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

{% docs raw_tmdb_search_id %}Unique identifier for one cached TMDB search response.{% enddocs %}
{% docs raw_tmdb_normalized_title %}Canonical title used for exact search-cache lookup.{% enddocs %}
{% docs raw_tmdb_search_query %}Human-readable title sent to the TMDB API.{% enddocs %}
{% docs raw_tmdb_language %}TMDB response language associated with the retrieval.{% enddocs %}
{% docs raw_tmdb_retrieved_at %}UTC timestamp at which the TMDB response was retrieved.{% enddocs %}
{% docs raw_tmdb_response_json %}Complete raw TMDB response retained for audit and reprocessing.{% enddocs %}
{% docs raw_tmdb_lookup_id %}Unique identifier for one source-evidence lookup context.{% enddocs %}
{% docs raw_tmdb_source_title %}Complete programme title preserved from the source schedule.{% enddocs %}
{% docs raw_tmdb_normalized_source_title %}Canonical source-title identity used for comparison.{% enddocs %}
{% docs raw_tmdb_production_year %}Production year explicitly extracted from source text.{% enddocs %}
{% docs raw_tmdb_query_titles_json %}Ordered source-derived query variants serialized as JSON.{% enddocs %}
{% docs raw_tmdb_used_query_override %}Whether a diagnostic query override selected the cached search.{% enddocs %}
{% docs raw_tmdb_created_at %}UTC timestamp at which the lookup context was recorded.{% enddocs %}
{% docs raw_tmdb_candidate_rank %}Candidate position in the supported TMDB response results.{% enddocs %}
{% docs raw_tmdb_id %}TMDB identifier interpreted together with the entity media type.{% enddocs %}
{% docs raw_tmdb_media_type %}TMDB entity type, constrained to movie or television.{% enddocs %}
{% docs raw_tmdb_title %}Localized title returned in the requested response language.{% enddocs %}
{% docs raw_tmdb_original_title %}Entity title in its original language.{% enddocs %}
{% docs raw_tmdb_original_language %}ISO code for the entity's original language when available.{% enddocs %}
{% docs raw_tmdb_release_date %}Movie release date or television first-air date when available.{% enddocs %}
{% docs raw_tmdb_overview %}Localized synopsis supplied by TMDB when available.{% enddocs %}
{% docs raw_tmdb_popularity %}Mutable TMDB popularity value at observation time.{% enddocs %}
{% docs raw_tmdb_vote_average %}Mutable TMDB average vote value from zero to ten.{% enddocs %}
{% docs raw_tmdb_vote_count %}Mutable number of TMDB votes at observation time.{% enddocs %}
{% docs raw_tmdb_resolution_id %}Unique identifier for one versioned scoring execution.{% enddocs %}
{% docs raw_tmdb_scoring_version %}Version of the deterministic candidate-scoring policy.{% enddocs %}
{% docs raw_tmdb_resolution_status %}Final entity-resolution outcome: matched or unresolved.{% enddocs %}
{% docs raw_tmdb_resolution_reason %}Machine-readable explanation for the resolution outcome.{% enddocs %}
{% docs raw_tmdb_winning_candidate_rank %}Source response rank of the highest-scoring candidate.{% enddocs %}
{% docs raw_tmdb_accepted_id %}Accepted TMDB ID, null when the resolution is unresolved.{% enddocs %}
{% docs raw_tmdb_accepted_media_type %}Accepted TMDB media type, null when unresolved.{% enddocs %}
{% docs raw_tmdb_winning_score %}Total confidence score of the highest-ranked candidate.{% enddocs %}
{% docs raw_tmdb_runner_up_score %}Total confidence score of the second-ranked candidate.{% enddocs %}
{% docs raw_tmdb_score_margin %}Difference between the winning and runner-up scores.{% enddocs %}
{% docs raw_tmdb_resolved_at %}UTC timestamp at which the resolution policy executed.{% enddocs %}
{% docs raw_tmdb_title_score %}Title-similarity component score from zero to one hundred.{% enddocs %}
{% docs raw_tmdb_year_score %}Production-year component score when explicit evidence exists.{% enddocs %}
{% docs raw_tmdb_total_score %}Weighted candidate confidence score from zero to one hundred.{% enddocs %}
{% docs raw_tmdb_score_rank %}Deterministic candidate position after scoring.{% enddocs %}
{% docs raw_tmdb_entity_detail_id %}Unique identifier for one full entity-details retrieval.{% enddocs %}
{% docs raw_tmdb_tagline %}Localized entity tagline when available.{% enddocs %}
{% docs raw_tmdb_runtime_minutes %}Movie runtime or first stated television episode runtime.{% enddocs %}
{% docs raw_tmdb_entity_status %}TMDB production or release status when available.{% enddocs %}
{% docs raw_tmdb_homepage %}Official entity homepage supplied by TMDB when available.{% enddocs %}
{% docs raw_tmdb_imdb_id %}IMDb identifier supplied directly by TMDB when available.{% enddocs %}
{% docs raw_tmdb_genres_json %}Ordered genre names serialized as JSON.{% enddocs %}
{% docs raw_tmdb_production_countries_json %}Ordered ISO production-country codes serialized as JSON.{% enddocs %}
{% docs raw_tmdb_production_companies_json %}Ordered production-company names serialized as JSON.{% enddocs %}
{% docs raw_tmdb_spoken_languages_json %}Ordered ISO spoken-language codes serialized as JSON.{% enddocs %}
{% docs raw_tmdb_metric_observation_id %}Unique identifier for one point-in-time metric observation.{% enddocs %}
{% docs raw_tmdb_observed_at %}UTC timestamp at which mutable metrics were observed.{% enddocs %}
