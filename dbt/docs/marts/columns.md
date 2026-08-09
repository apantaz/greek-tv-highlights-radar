{% docs mart_daily_highlights_observation_id %}Exact current broadcast observation ranked by the mart.{% enddocs %}
{% docs mart_daily_highlights_channel_key %}Foreign key to the channel dimension.{% enddocs %}
{% docs mart_daily_highlights_programme_key %}Foreign key to the canonical programme dimension.{% enddocs %}
{% docs mart_daily_highlights_tmdb_id %}TMDB entity identifier behind the ranked programme.{% enddocs %}
{% docs mart_daily_highlights_media_type %}TMDB entity type: movie or television.{% enddocs %}
{% docs mart_daily_highlights_match_confidence %}Resolver confidence, from zero to 100, that the schedule title maps to the selected TMDB entity.{% enddocs %}
{% docs mart_daily_highlights_source %}Upstream schedule source containing the broadcast.{% enddocs %}
{% docs mart_daily_highlights_channel %}Channel whose daily highlights include the broadcast.{% enddocs %}
{% docs mart_daily_highlights_schedule_date %}Requested schedule date within which the broadcast is ranked.{% enddocs %}
{% docs mart_daily_highlights_programme_position %}Original chronological position in the channel schedule.{% enddocs %}
{% docs mart_daily_highlights_schedule_title %}Programme title exactly as observed in the schedule.{% enddocs %}
{% docs mart_daily_highlights_starts_at_local %}Athens-local scheduled start timestamp.{% enddocs %}
{% docs mart_daily_highlights_programme_title %}Preferred localized canonical programme title.{% enddocs %}
{% docs mart_daily_highlights_original_title %}Canonical programme title in its original language.{% enddocs %}
{% docs mart_daily_highlights_release_year %}Release or first-air year when supplied by TMDB.{% enddocs %}
{% docs mart_daily_highlights_runtime_minutes %}Movie runtime or first stated episode runtime supplied by TMDB.{% enddocs %}
{% docs mart_daily_highlights_metadata_retrieved_at %}Timestamp when the canonical TMDB metadata was retrieved.{% enddocs %}
{% docs mart_daily_highlights_imdb_id %}IMDb identifier supplied by TMDB when available.{% enddocs %}
{% docs mart_daily_highlights_poster_path %}Relative TMDB poster path used by presentation clients.{% enddocs %}
{% docs mart_daily_highlights_genres_json %}Complete canonical genre collection retained as JSON.{% enddocs %}
{% docs mart_daily_highlights_metric_observation_id %}Latest TMDB metric observation used by ranking version `v1`.{% enddocs %}
{% docs mart_daily_highlights_popularity %}Raw TMDB popularity value used by the popularity component.{% enddocs %}
{% docs mart_daily_highlights_vote_average %}Raw TMDB vote average used by the quality component.{% enddocs %}
{% docs mart_daily_highlights_vote_count %}Raw TMDB vote count used by the confidence component.{% enddocs %}
{% docs mart_daily_highlights_metrics_observed_at %}Timestamp of the metric observation used for ranking.{% enddocs %}
{% docs mart_daily_highlights_quality_score %}Vote average normalized linearly from zero to 100.{% enddocs %}
{% docs mart_daily_highlights_confidence_score %}Vote count normalized from zero to 100 on a base-10 logarithmic scale and capped at 100.{% enddocs %}
{% docs mart_daily_highlights_popularity_score %}Non-negative popularity normalized from zero to 100 on a base-10 logarithmic scale and capped at 100.{% enddocs %}
{% docs mart_daily_highlights_highlight_score %}Weighted score: 70% quality, 20% confidence, and 10% popularity.{% enddocs %}
{% docs mart_daily_highlights_highlight_rank %}Deterministic score order within source, channel, and requested schedule date.{% enddocs %}
{% docs mart_daily_highlights_overall_highlight_rank %}Deterministic score order across every channel within a source and requested schedule date.{% enddocs %}
{% docs mart_daily_highlights_ranking_version %}Version of the eligibility and scoring policy, currently `v1`.{% enddocs %}
{% docs mart_daily_highlights_ranking_explanation %}Human-readable summary of the scoring weights.{% enddocs %}

{% docs mart_daily_enrichment_coverage_channel_key %}Foreign key to the channel dimension.{% enddocs %}
{% docs mart_daily_enrichment_coverage_source %}Upstream schedule source measured by the row.{% enddocs %}
{% docs mart_daily_enrichment_coverage_channel %}Channel measured by the row.{% enddocs %}
{% docs mart_daily_enrichment_coverage_schedule_date %}Requested schedule date measured by the row.{% enddocs %}
{% docs mart_daily_enrichment_coverage_programme_count %}All current broadcast observations in the schedule.{% enddocs %}
{% docs mart_daily_enrichment_coverage_submitted %}Broadcasts linked to an enrichment lookup.{% enddocs %}
{% docs mart_daily_enrichment_coverage_resolved %}Broadcasts with a persisted matched or unresolved decision.{% enddocs %}
{% docs mart_daily_enrichment_coverage_matched %}Broadcasts confidently matched to a TMDB identity.{% enddocs %}
{% docs mart_daily_enrichment_coverage_unresolved %}Broadcasts deliberately left unresolved by the scoring policy.{% enddocs %}
{% docs mart_daily_enrichment_coverage_canonical %}Broadcasts linked to a canonical programme with retrieved metadata.{% enddocs %}
{% docs mart_daily_enrichment_coverage_missing %}Broadcasts not yet linked to an enrichment lookup.{% enddocs %}
{% docs mart_daily_enrichment_coverage_missing_metadata %}Matched broadcasts awaiting canonical entity metadata.{% enddocs %}
{% docs mart_daily_enrichment_coverage_enrichment_pct %}Percentage of all broadcasts linked to enrichment lookups.{% enddocs %}
{% docs mart_daily_enrichment_coverage_resolution_pct %}Percentage of all broadcasts with persisted resolution decisions.{% enddocs %}
{% docs mart_daily_enrichment_coverage_match_pct %}Percentage of resolved broadcasts that matched confidently; null without resolutions.{% enddocs %}
{% docs mart_daily_enrichment_coverage_canonical_pct %}Percentage of all broadcasts carrying canonical programme identity.{% enddocs %}
{% docs mart_daily_enrichment_coverage_ingestion_completed_at %}Completion timestamp of the successful ingestion represented by the schedule.{% enddocs %}

{% docs fct_tmdb_metrics_metric_observation_id %}
Primary key of the immutable point-in-time metric observation.
{% enddocs %}

{% docs fct_tmdb_metrics_entity_detail_id %}
Entity-detail retrieval that produced the metric observation.
{% enddocs %}

{% docs fct_tmdb_metrics_programme_key %}
Foreign key to the canonical programme dimension.
{% enddocs %}

{% docs fct_tmdb_metrics_tmdb_id %}
Stable TMDB identifier interpreted within the media type.
{% enddocs %}

{% docs fct_tmdb_metrics_media_type %}
TMDB entity namespace: movie or television series.
{% enddocs %}

{% docs fct_tmdb_metrics_popularity %}
Mutable TMDB popularity value at observation time.
{% enddocs %}

{% docs fct_tmdb_metrics_vote_average %}
Mutable TMDB average vote value from zero to ten at observation time.
{% enddocs %}

{% docs fct_tmdb_metrics_vote_count %}
Mutable TMDB vote count at observation time.
{% enddocs %}

{% docs fct_tmdb_metrics_observed_at %}
Exact timezone-aware timestamp at which TMDB returned the metrics.
{% enddocs %}

{% docs fct_tmdb_metrics_observation_date %}
UTC calendar date derived from the observation timestamp.
{% enddocs %}

{% docs dim_programmes_programme_key %}
Deterministic surrogate key generated from media type and TMDB ID.
{% enddocs %}

{% docs dim_programmes_entity_detail_id %}
Selected latest entity-detail response backing the dimension row.
{% enddocs %}

{% docs dim_programmes_tmdb_id %}
Stable TMDB identifier interpreted within the programme media type.
{% enddocs %}

{% docs dim_programmes_media_type %}
TMDB entity namespace: movie or television series.
{% enddocs %}

{% docs dim_programmes_metadata_language %}
Response language of the selected descriptive metadata, preferring `el-GR`.
{% enddocs %}

{% docs dim_programmes_title %}
Localized programme title from the selected TMDB detail response.
{% enddocs %}

{% docs dim_programmes_original_title %}
Original title supplied by TMDB.
{% enddocs %}

{% docs dim_programmes_original_language %}
Original production language code supplied by TMDB.
{% enddocs %}

{% docs dim_programmes_release_date %}
Movie release date or television first-air date.
{% enddocs %}

{% docs dim_programmes_release_year %}
Calendar year derived from the release or first-air date.
{% enddocs %}

{% docs dim_programmes_overview %}
Localized TMDB synopsis, when available.
{% enddocs %}

{% docs dim_programmes_tagline %}
Localized TMDB tagline, when available.
{% enddocs %}

{% docs dim_programmes_runtime_minutes %}
Movie runtime or representative episode runtime in minutes, when available.
{% enddocs %}

{% docs dim_programmes_status %}
Current production or release status reported by TMDB.
{% enddocs %}

{% docs dim_programmes_homepage %}
Official homepage URL reported by TMDB, when available.
{% enddocs %}

{% docs dim_programmes_imdb_id %}
IMDb identifier reported by TMDB, when available.
{% enddocs %}

{% docs dim_programmes_poster_path %}
Relative TMDB poster asset path, when available.
{% enddocs %}

{% docs dim_programmes_genres_json %}
Complete normalized genre collection retained as JSON.
{% enddocs %}

{% docs dim_programmes_production_countries_json %}
Complete normalized production-country collection retained as JSON.
{% enddocs %}

{% docs dim_programmes_production_companies_json %}
Complete normalized production-company collection retained as JSON.
{% enddocs %}

{% docs dim_programmes_spoken_languages_json %}
Complete normalized spoken-language collection retained as JSON.
{% enddocs %}

{% docs dim_programmes_metadata_retrieved_at %}
UTC retrieval timestamp of the selected entity-detail response.
{% enddocs %}

{% docs dim_channels_channel_key %}
Deterministic surrogate key generated from source and channel.
{% enddocs %}

{% docs dim_channels_source %}
Upstream schedule source represented by the channel.
{% enddocs %}

{% docs dim_channels_channel %}
Channel display name observed in successful schedules.
{% enddocs %}

{% docs dim_channels_first_schedule_date %}
Earliest requested schedule date currently represented for the channel.
{% enddocs %}

{% docs dim_channels_latest_schedule_date %}
Latest requested schedule date currently represented for the channel.
{% enddocs %}

{% docs dim_channels_first_observed_at %}
Earliest retrieval timestamp among the channel's current schedules.
{% enddocs %}

{% docs dim_channels_latest_observed_at %}
Latest retrieval timestamp among the channel's current schedules.
{% enddocs %}

{% docs fct_current_broadcasts_observation_id %}
Primary key of the programme observation in its selected ingestion run.
{% enddocs %}

{% docs fct_current_broadcasts_broadcast_id %}
Source-observation identifier derived from schedule attributes.
{% enddocs %}

{% docs fct_current_broadcasts_run_id %}
Latest successful ingestion run that produced the programme observation.
{% enddocs %}

{% docs fct_current_broadcasts_channel_key %}
Foreign key to the channel dimension.
{% enddocs %}

{% docs fct_current_broadcasts_programme_key %}
Nullable foreign key to the canonical programme dimension when matched metadata exists.
{% enddocs %}

{% docs fct_current_broadcasts_lookup_id %}
Nullable enrichment lookup evaluated for the exact broadcast observation.
{% enddocs %}

{% docs fct_current_broadcasts_resolution_id %}
Nullable latest resolution associated with the broadcast's enrichment lookup.
{% enddocs %}

{% docs fct_current_broadcasts_resolution_status %}
Matched or unresolved outcome; null when the broadcast has not been enriched.
{% enddocs %}

{% docs fct_current_broadcasts_match_confidence %}
Confidence score, from zero to 100, of the selected schedule-to-TMDB identity match.
Policy `v1` requires at least 85 and a winner margin of at least 10 when another
candidate exists. This score documents resolution and does not guarantee that full
entity metadata has already been retrieved.
{% enddocs %}

{% docs fct_current_broadcasts_tmdb_id %}
Nullable TMDB identifier accepted for a confidently matched broadcast.
{% enddocs %}

{% docs fct_current_broadcasts_media_type %}
Nullable TMDB namespace, movie or television, for the accepted identity.
{% enddocs %}

{% docs fct_current_broadcasts_source %}
Upstream schedule source associated with the programme.
{% enddocs %}

{% docs fct_current_broadcasts_channel %}
Channel associated with the programme.
{% enddocs %}

{% docs fct_current_broadcasts_schedule_date %}
Date requested from the source for the selected schedule.
{% enddocs %}

{% docs fct_current_broadcasts_broadcast_date %}
Athens-local calendar date on which the programme starts.
{% enddocs %}

{% docs fct_current_broadcasts_title %}
Programme title as observed in the current source schedule.
{% enddocs %}

{% docs fct_current_broadcasts_starts_at %}
Timezone-aware programme start timestamp.
{% enddocs %}

{% docs fct_current_broadcasts_ends_at %}
Timezone-aware programme end timestamp, when the following programme is known.
{% enddocs %}

{% docs fct_current_broadcasts_starts_at_local %}
Programme start represented as an Athens-local timestamp.
{% enddocs %}

{% docs fct_current_broadcasts_ends_at_local %}
Programme end represented as an Athens-local timestamp, when known.
{% enddocs %}

{% docs fct_current_broadcasts_duration_minutes %}
Scheduled minutes between start and end; null when the end is unknown.
{% enddocs %}

{% docs fct_current_broadcasts_crosses_midnight %}
Whether the programme starts and ends on different Athens-local calendar dates.
{% enddocs %}

{% docs fct_current_broadcasts_programme_position %}
One-based chronological position within the source, channel, and requested date.
{% enddocs %}

{% docs fct_current_broadcasts_description %}
Optional programme description supplied by the source.
{% enddocs %}

{% docs fct_current_broadcasts_source_url %}
Upstream page from which the programme was parsed.
{% enddocs %}

{% docs fct_current_broadcasts_retrieved_at %}
UTC timestamp at which the schedule response was retrieved.
{% enddocs %}

{% docs fct_current_broadcasts_ingestion_completed_at %}
UTC timestamp at which the selected ingestion run completed.
{% enddocs %}

{% docs mart_daily_channel_schedule_channel_key %}
Foreign key to the channel dimension.
{% enddocs %}

{% docs mart_daily_channel_schedule_source %}
Upstream schedule source summarized by the row.
{% enddocs %}

{% docs mart_daily_channel_schedule_channel %}
Channel summarized by the row.
{% enddocs %}

{% docs mart_daily_channel_schedule_schedule_date %}
Requested schedule date summarized by the row.
{% enddocs %}

{% docs mart_daily_channel_schedule_programme_count %}
Number of current programme observations in the schedule.
{% enddocs %}

{% docs mart_daily_channel_schedule_programmes_with_known_duration %}
Number of programmes for which both start and end timestamps are available.
{% enddocs %}

{% docs mart_daily_channel_schedule_known_scheduled_minutes %}
Sum of scheduled minutes for programmes with known end timestamps.
{% enddocs %}

{% docs mart_daily_channel_schedule_first_programme_starts_at_local %}
Earliest Athens-local programme start in the requested schedule.
{% enddocs %}

{% docs mart_daily_channel_schedule_last_programme_ends_at_local %}
Latest known Athens-local programme end in the requested schedule.
{% enddocs %}

{% docs mart_daily_channel_schedule_programmes_crossing_midnight %}
Number of programmes spanning two Athens-local calendar dates.
{% enddocs %}

{% docs mart_daily_channel_schedule_ingestion_completed_at %}
Completion timestamp of the successful ingestion run represented by the schedule.
{% enddocs %}
