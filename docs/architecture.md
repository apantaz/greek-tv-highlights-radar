# Architecture

## Ingestion architecture

```text
CLI
 └─ Ingestion orchestrator
     ├─ ingestion_runs: running
     ├─ ScheduleClient: bounded retry
     ├─ immutable raw snapshot: channel/date/run_id.html
     ├─ ProgrammaTileorasis parser
     ├─ schedule quality checks
     └─ atomic persistence
         ├─ broadcast_observations: append-only
         └─ ingestion_runs: succeeded or failed

latest successful run per source/channel/date
 └─ current_broadcasts view
```

The source page is addressed by channel ID, channel name, and broadcast date. The
parser selects only the matching channel table and ignores navigation rows. When the
displayed times wrap from late evening to early morning, subsequent broadcasts are
assigned to the next calendar day in the `Europe/Athens` timezone.

A typed discovery adapter parses source identifiers and display names from the
source's `.channels_list` element. Known source identifiers receive stable readable
aliases, while a newly advertised identifier receives a `channel-<id>` fallback.
Every single-channel and batch invocation therefore uses the catalog currently
advertised by the source instead of assuming static membership.

Catalog discovery is a precondition to creating an ingestion run because the run's
channel identity and source URL are not known beforehand. Once resolved, schedule
fetching and parsing remain inside the audited run boundary.

## Batch boundary

```text
discover catalog once
 └─ for each channel, sequentially
     ├─ create an independent ingestion run
     ├─ fetch, snapshot, parse, validate, and persist
     ├─ capture success or failure in the batch result
     └─ continue with the next channel
```

Batch orchestration is deliberately sequential to avoid unnecessary load on the
public source. Channel failures are returned as structured results rather than
propagated from the loop. A catalog-discovery failure prevents the batch from
starting because there is no trustworthy set of channels to process.

There is no persisted batch entity in the current model. Each channel attempt already
has a complete audit record in `ingestion_runs`; a separate batch table would add
state without a demonstrated analytical or operational need.

## Transformation boundary

The repository-local dbt project connects to the ingestion DuckDB file and declares
`ingestion_runs` and `broadcast_observations` as sources in the `main` schema. Python
owns ingestion and immutable source data; dbt owns derived analytical schemas and
must not mutate ingestion relations.

The dbt development target uses `greek_tv` as a namespace. Folder-level schema
configuration writes raw models to `greek_tv_raw`, intermediate models to
`greek_tv_intermediate`, and marts to `greek_tv_marts`. Model descriptions are
persisted on relations and columns so the warehouse remains self-documenting.
Seeds share the `greek_tv_raw` schema, timestamp-strategy snapshots target
`snapshots`, and data-test failures are not persisted by default.

The raw layer exposes `raw_ingestion_runs` and `raw_broadcast_observations` as views.
It preserves source grains and column meaning while enforcing source-boundary
contracts through dbt tests. Intermediate, dimensional, and mart models are added as
separately reviewable deliveries.

The intermediate layer ranks successful runs within each
`source/channel/schedule_date` partition by completion time, start time, and run ID.
`int_current_broadcasts` joins observations only to those selected runs, providing a
deterministic current schedule without deleting superseded history.

The mart layer materializes three consumer-facing tables. `dim_channels` provides a
stable source-and-channel key, `fct_current_broadcasts` adds Athens-local schedule
attributes at programme-observation grain, and `mart_daily_channel_schedule`
aggregates those facts to one row per source, channel, and requested date.

## Data grains

See the [data model](data-model.md) for the current entity-relationship diagram and
view lineage.

- `ingestion_runs`: one attempted fetch for one source, channel, and requested date.
- `broadcast_observations`: one programme row observed in one ingestion run.
- `current_broadcasts`: programmes from the latest successful run for each
  source/channel/date partition.
- `int_latest_successful_ingestion_runs`: dbt-owned latest successful run per
  source/channel/date partition.
- `int_current_broadcasts`: dbt-owned programme observations for those selected runs.
- `dim_channels`: one currently represented source and channel.
- `fct_current_broadcasts`: one current programme observation enriched for analysis.
- `mart_daily_channel_schedule`: one source/channel/requested-date schedule summary.
- `broadcasts`: preserved milestone-one table; migrated non-destructively and retained
  for audit compatibility.

`Broadcast` is still a source observation, not a canonical film or television
programme. Later enrichment will introduce a separate canonical programme entity
instead of overwriting source data.

## Enrichment boundary

Title normalization is a deterministic preparation step for external metadata
searches. It keeps the whitespace-normalized source title alongside a case-, accent-,
and punctuation-neutral search title. Only explicit schedule annotations are
extracted: a leading content rating and a trailing repeat marker.

The normalizer deliberately does not interpret season numerals, programme types, or
parenthesized alternate titles. Those values can affect entity resolution and remain
part of the searchable title until candidate scoring has enough evidence to handle
them. The original observation remains authoritative and is never overwritten.

A separate evidence extractor identifies Latin-script titles explicitly supplied in
parentheses or at the start of a bracketed description. It also captures a stated
production year. International variants are searched before the localized title, but
their presence is evidence only—not an accepted match.

TMDB retrieval sends a human-readable search title with accents preserved, while its
canonical normalized form and requested response language act as the cache key. An
explicit query override is retained for diagnostic commands, but unattended
processing uses only source-derived evidence and leaves insufficient evidence
unresolved. A cache miss makes one authenticated multi-search request; a cache hit
returns the latest stored result without network access. Explicit refreshes append a
new search rather than replacing history.

```text
source title
  -> deterministic normalized title
  -> latest exact-query cache lookup
      -> cache hit: stored candidates
      -> cache miss/refresh: TMDB multi-search
          -> tmdb_searches: immutable raw JSON response
          -> tmdb_candidates: ordered movie and TV candidates
          -> tmdb_lookup_contexts: source evidence linked to selected search
```

People and malformed results are excluded from the typed candidate table but remain
available in the raw JSON. Candidate response order is descriptive API metadata, not
an entity-resolution decision.

Lookup context is stored separately from the reusable query cache. Every command
records the complete source title, canonical source identity, extracted production
year, ordered query variants, override usage, and selected search ID. Candidate
scoring can therefore use source-specific evidence even when several observations
reuse the same cached TMDB response.

## Resolution boundary

Candidate resolution is deterministic, versioned, and append-only. Scoring version
`v1` compares the selected search query with both the localized and original TMDB
candidate titles. When a source production year exists, title similarity contributes
75% of the total and year agreement contributes 25%; without year evidence, title
similarity is the total score.

A candidate is matched only when it reaches 85 points and leads the runner-up by at
least 10 points. No candidates, a weak winner, or an ambiguous margin produces an
explicit unresolved outcome. Popularity and vote metrics do not contribute because
they change over time and do not establish identity. Every component score and final
reason is retained; unresolved resolution rows keep their accepted `tmdb_id` and
`media_type` fields null. There is no manual override or review workflow.

## Batch enrichment boundary

The unattended batch reads distinct title-and-description combinations from the
ingestion-owned `current_broadcasts` view. Equivalent extracted evidence is processed
once per response language and scoring-policy version. Evidence with an existing
resolution is skipped; new evidence reuses exact-query caches before making a TMDB
request.

```text
distinct current title + description
  -> extract explicit title variants and production year
  -> skip equivalent resolved evidence
  -> cached search or sequential TMDB request
  -> append lookup context and versioned resolution
  -> continue after title-level failure
  -> aggregate matched/unresolved/skipped/failed/cache counts
```

Processing remains sequential to keep upstream request behavior predictable. An
optional limit supports controlled incremental runs. Optional channel and requested
schedule-date filters join current broadcasts back to their ingestion runs before
evidence is deduplicated. Unresolved identity is a valid outcome; only operational
failures make the command exit non-zero.

The source website's search menu does not expose an IMDb identifier. Its client-side
JavaScript constructs a Google query in the form `site:imdb.com <displayed title>`.
Because that adds no identity evidence and search ranking is external and unstable,
the pipeline does not scrape or trust the first Google result.

## Failure boundary

The run record is created before network access. Fetch, snapshot, parse, quality, or
persistence errors close it as `failed` with a bounded error message. Observations and
the successful status update share one database transaction, preventing a run from
being marked successful with partial observations.

Raw snapshots are excluded from Git because they may contain large amounts of
third-party content. Each response is stored under its run identifier and is never
overwritten. A reduced fixture documents the upstream HTML contract and makes parser
tests reproducible.
