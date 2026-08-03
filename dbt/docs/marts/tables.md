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
midnight-crossing behavior, and deterministic schedule position.

{% enddocs %}

{% docs mart_daily_channel_schedule %}

# Daily channel schedule mart

One row per source, channel, and requested schedule date. This consumer-facing mart
summarizes programme volume, known scheduled minutes, daily boundaries, and
programmes that cross midnight.

{% enddocs %}
