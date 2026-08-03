# Architecture Decision Records

## ADR-001
DuckDB chosen for local analytical storage.

DuckDB keeps the portfolio project runnable without infrastructure while supporting
analytical SQL and the repository-local dbt layer. A hosted, concurrent product would revisit
this decision.

## ADR-002
Raw source observations are preserved before parsing.

This enables parser debugging and future reprocessing without repeatedly requesting
the upstream site.

## ADR-003
The first release supports one source and one channel.

A narrow end-to-end slice demonstrates reliability and exposes real data problems
before abstractions for multiple sources are introduced.

## ADR-004
Ingestion history is append-only and current state is a derived view.

Schedules may change between collection attempts. Storing observations by run keeps
those changes auditable, while `current_broadcasts` provides a convenient consumer
interface based on the latest successful run. Failed runs cannot replace a valid
current schedule.

## ADR-005
The milestone-one table is migrated without destructive schema changes.

Existing `broadcasts` records are copied into deterministic legacy ingestion runs and
observations. The original table remains intact. This favors recoverability and makes
the migration safe to execute repeatedly.

## ADR-006
Retries are bounded and limited to transient failures.

Transport failures and selected temporary HTTP statuses use exponential backoff.
Permanent client errors fail immediately, avoiding unnecessary load on the source and
making configuration or URL problems visible.

## ADR-007
Channel membership is discovered from the source at runtime.

Source identifiers and display names are parsed from `.channels_list` before
ingestion. Known identifiers receive stable lowercase aliases for usability, but the
alias mapping does not determine catalog membership. Newly added channels are exposed
through their numeric identifier and a `channel-<id>` fallback; removed channels stop
resolving. This avoids silently freezing a changing upstream catalog in application
code.

## ADR-008
Batch ingestion isolates channels without introducing a persisted batch entity.

The catalog is discovered once and channels are processed sequentially to limit load
on the public source. Each channel uses the existing audited ingestion-run boundary,
and failures are captured as structured batch results so later channels continue.
The command returns a non-zero status for any partial failure. A separate batch table
is deferred until a concrete requirement exists for persisted batch-level metadata.

## ADR-009
dbt configuration is repository-local and ingestion relations are read-only sources.

The dbt project and DuckDB profile live under `dbt/`, making setup reproducible
without user-specific configuration. The database path remains environment-
overridable for local development and CI. Python retains ownership of immutable
ingestion tables, while dbt is limited to derived analytical relations. This keeps
the write boundary explicit and prevents transformations from altering source
history.

## ADR-010
Raw dbt models are views that preserve source grain.

The first transformation layer selects explicit source columns without introducing
business logic. Views keep local builds lightweight and avoid duplicating immutable
ingestion data. Tests define the source contract before downstream transformations
depend on it; intermediate models will own reusable business logic.

## ADR-011
Current schedules are selected deterministically in the dbt intermediate layer.

Successful runs are ranked within each source, channel, and requested schedule date
by completion timestamp, start timestamp, and run identifier. The final tie-breaker
prevents database row order from influencing current state. Observations are joined
to the selected run IDs, preserving full history upstream while giving marts a stable
current-schedule interface.

## ADR-012
Business-facing schedule models are materialized as tables.

The channel dimension, current-broadcast fact, and daily schedule mart are small,
stable consumer interfaces. Materializing them as tables makes query behavior
predictable and separates consumers from upstream view execution. Each model declares
its materialization explicitly; future scale changes should be driven by measurement.

## ADR-013
Title normalization is deterministic and never replaces the source title.

External metadata searches need titles that are insensitive to case, accents,
punctuation, and incidental whitespace. The normalizer therefore produces a separate
search value and extracts only explicit leading content ratings and trailing repeat
markers. It does not infer programme type, season, or alternate-title meaning. This
keeps future candidate matching reproducible, explainable, and auditable against the
original schedule observation.

## ADR-014
TMDB responses and candidates are cached append-only before entity resolution.

The canonical normalized title and response language form the exact cache lookup,
while the API receives and records a human-readable query with accents preserved. A
diagnostic command can explicitly test an international title without changing
source evidence; unattended processing uses source-derived evidence only. A cache
miss stores the complete raw multi-search response and ordered, typed movie and
television candidates in one transaction; an explicit refresh creates new history.
People and malformed results remain auditable in the raw JSON but do not enter
candidate rows. No returned rank is interpreted as an accepted match. This limits
network usage while keeping future scoring reproducible against the evidence
available at retrieval time.

## ADR-015
Only explicit schedule metadata becomes automatic title evidence.

Latin-script titles supplied in parentheses or leading description brackets become
additional TMDB search variants, and stated production years are retained for later
scoring. The source site's IMDb menu is not an identifier: it constructs a Google
`site:imdb.com` query from the same displayed title. Google result order is therefore
excluded from the deterministic pipeline. Missing international titles remain
unresolved rather than receiving an inferred translation or manual correction.

## ADR-016
Source lookup context is separate from the reusable TMDB response cache.

The same external query may support multiple schedule observations, while their
source titles and production-year evidence can differ. Each lookup therefore appends
a context row linked to the selected cached search. This avoids duplicating API
responses without discarding the observation-specific evidence required for
explainable candidate scoring.

## ADR-017
Entity resolution is conservative, automatic, and allowed to remain unresolved.

Scoring version `v1` uses deterministic title similarity and explicit production-year
evidence. A match must clear both a confidence threshold and a winner-margin threshold.
Popularity and vote counts are excluded because they are mutable and do not prove
identity. Weak, tied, and missing results persist as unresolved rather than being
forced into a match. The project intentionally has no manual review or override path,
keeping execution unattended and reproducible.

## ADR-018
Batch enrichment is evidence-idempotent, sequential, and failure-isolated.

Distinct current schedule text is reduced to explicit title variants and production
year evidence. A combination already resolved under the same response language and
scoring version is skipped, while external search responses are reused through the
query cache. New requests run sequentially and a title-level failure does not prevent
later programmes from completing. Unresolved matches count as successful processing;
only operational failures produce a non-zero command status.

## ADR-019
Full metadata retrieval is gated by accepted identity and cached append-only.

Only matched resolutions may produce detail requests. The stable cache key combines
media type, TMDB ID, and response language because numeric IDs are interpreted within
an entity type and descriptive text can be localized. Complete responses are retained
for audit, while normalized columns expose stable descriptive attributes. Popularity,
vote average, and vote count are excluded from those columns because they are mutable;
they require a separate timestamped observation model. Retrieval is sequential and
failure-isolated, and refreshes append evidence rather than replacing it.

## ADR-020
Mutable TMDB metrics use bounded, append-only observations.

Popularity, vote average, and vote count describe a point in time and therefore do
not belong in stable normalized entity columns. Each details response produces one
metric observation in the same transaction. A configurable maximum age, defaulting
to 24 hours, controls whether another request is due; fresh batches construct no API
client. Existing raw detail responses provide a non-destructive historical baseline.
Operational failures remain isolated, and a zero-hour boundary provides an explicit
forced-refresh mechanism without a separate mutation path.

## ADR-021
Broadcast enrichment lineage is persisted by stable identifiers.

Each current broadcast observation is linked directly to the lookup context evaluated
for it. The append-only bridge is idempotent at observation, lookup, and scoring-version
grain and is populated for both newly processed and cached evidence. dbt uses this
relationship to expose enrichment at broadcast grain while retaining unlinked and
unresolved observations. Title-based inference is prohibited because matching text is
not a durable lineage key.
