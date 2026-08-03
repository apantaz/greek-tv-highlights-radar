{% docs raw_ingestion_runs %}

# Raw ingestion runs

Typed, analysis-ready projection of immutable ingestion attempts. The model preserves
the source grain of one row per attempted source, channel, and schedule date
ingestion.

{% enddocs %}

{% docs raw_tmdb_searches %}

# Raw TMDB searches

Source-aligned projection of immutable TMDB multi-search responses. The grain is one
external request for an exact normalized query and response language.

{% enddocs %}

{% docs raw_tmdb_lookup_contexts %}

# Raw TMDB lookup contexts

Source-aligned evidence connecting one observed programme title and its explicit
production metadata to the cached TMDB search selected for scoring.

{% enddocs %}

{% docs raw_tmdb_candidates %}

# Raw TMDB candidates

Ordered movie and television candidates returned by a cached TMDB search. Candidate
rank is response metadata and does not represent an accepted identity.

{% enddocs %}

{% docs raw_tmdb_resolutions %}

# Raw TMDB resolutions

Append-only, versioned entity-resolution outcomes. Matched rows carry an accepted
TMDB identity, while unresolved rows deliberately leave that identity null.

{% enddocs %}

{% docs raw_tmdb_candidate_scores %}

# Raw TMDB candidate scores

Auditable component scores for every candidate evaluated during one resolution run.
The composite grain is resolution execution and source candidate rank.

{% enddocs %}

{% docs raw_tmdb_entity_details %}

# Raw TMDB entity details

Immutable full-detail responses retrieved only for confidently matched movie and
television identities. Multiple languages and retrieval times are retained.

{% enddocs %}

{% docs raw_tmdb_entity_metric_observations %}

# Raw TMDB entity metric observations

Append-only point-in-time observations of mutable popularity and voting metrics. Each
row is tied to the exact entity-details response that supplied its values.

{% enddocs %}

{% docs raw_broadcast_observations %}

# Raw broadcast observations

Typed, analysis-ready projection of programme observations. The model preserves the
source grain of one programme row observed during one successful ingestion run.

{% enddocs %}
