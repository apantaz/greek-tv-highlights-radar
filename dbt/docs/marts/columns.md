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
