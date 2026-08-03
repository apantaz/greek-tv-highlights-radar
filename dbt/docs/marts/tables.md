{% docs mart_daily_enrichment_coverage %}

# Daily enrichment coverage mart

One row per source, channel, and requested schedule date. The mart reports how many
current broadcasts entered enrichment, reached a resolution, matched confidently,
and obtained canonical metadata. Coverage rates retain all broadcasts as the primary
denominator; match rate uses resolved broadcasts and is null when none were resolved.

{% enddocs %}

{% docs fct_tmdb_metrics %}

# Historical TMDB metrics fact

One row per immutable TMDB metric observation. The fact connects every popularity,
vote-average, and vote-count snapshot to the canonical programme dimension while
preserving the original UTC observation timestamp for trend analysis.

{% enddocs %}

{% docs dim_programmes %}

# Programme dimension

One row per confidently matched TMDB identity. The dimension uses a deterministic
surrogate key derived from media type and TMDB ID, prefers Greek localized metadata
when available, and exposes the latest stable descriptive attributes. Mutable
popularity and voting metrics are deliberately excluded.

{% enddocs %}

{% docs dim_channels %}

# Channel dimension

One row per source and channel currently represented by a successful schedule. The
dimension supplies a stable surrogate key and the observed schedule-date range for
joining business-facing broadcast models.

{% enddocs %}

{% docs fct_current_broadcasts %}

# Current broadcast fact

One row per programme observation in the latest successful schedule for a source,
channel, and requested date. The fact adds Athens-local timestamps, duration,
midnight-crossing behavior, deterministic schedule position, and nullable canonical
programme identity. Unresolved and unenriched broadcasts remain in the fact.

{% enddocs %}

{% docs mart_daily_channel_schedule %}

# Daily channel schedule mart

One row per source, channel, and requested schedule date. This consumer-facing mart
summarizes programme volume, known scheduled minutes, daily boundaries, and
programmes that cross midnight.

{% enddocs %}
