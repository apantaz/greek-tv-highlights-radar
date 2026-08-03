# Roadmap

The `v0.7.0` release completes the enrichment warehouse with direct broadcast
lineage, canonical programme identity, programme-aware facts, historical TMDB
metrics, and daily enrichment coverage. Transparent highlight ranking and the
Streamlit analytics product follow.

## Milestone 1 — ERT1 vertical slice

- [x] Date-addressable HTTP client
- [x] Raw HTML snapshots
- [x] Typed broadcast parser
- [x] Midnight rollover handling
- [x] Idempotent DuckDB persistence
- [x] Offline parser and persistence tests
- [x] Ruff and pytest CI

## Milestone 2 — Reliable multi-channel ingestion

- [x] Add retries with bounded backoff
- [x] Record structured ingestion-run metadata and failures
- [x] Store immutable run-addressed raw snapshots
- [x] Preserve append-only observations and derive the current schedule
- [x] Enforce schedule quality thresholds
- [x] Migrate milestone-one databases non-destructively
- [x] Add representative commercial and public channels
- [x] Add batch ingestion with isolated per-channel failures

## Milestone 3 — Analytics warehouse foundation (`v0.4.0`)

- [x] Configure a repository-local dbt-duckdb project
- [x] Declare ingestion relations as documented dbt sources
- [x] Add reproducible direct dbt commands and CI/pre-push validation
- [x] Add raw models and source-boundary tests
- [x] Add intermediate latest-successful-run logic
- [x] Add dimensional, fact, and initial mart models
- [x] Generate dbt documentation and lineage artifacts

## Milestone 4 — Enrichment and entity resolution (`v0.5.0`)

- [x] Normalize Greek and international titles deterministically
- [x] Retrieve and cache TMDB candidates with immutable raw responses
- [x] Score candidates with conservative automatic resolution and unresolved outcomes

## Milestone 5 — Matched entity metadata (`v0.6.0`)

- [x] Automate idempotent batch enrichment across distinct current programmes
- [x] Retrieve full details only for confidently matched TMDB entities
- [x] Cache stable entity metadata by media type, TMDB ID, and language
- [x] Snapshot mutable voting and popularity metrics on a bounded refresh interval
- [x] Project every enrichment source into documented, tested dbt raw views
- [x] Expose latest resolution, entity metadata, and metrics through tested intermediate models

## Milestone 6 — Enrichment marts (`v0.7.0`)

- [x] Persist direct broadcast-to-lookup lineage without title-based inference
- [x] Build a canonical programme dimension
- [x] Add nullable programme identity to the current-broadcast fact
- [x] Publish historical TMDB metric observations as a fact
- [x] Build enrichment-coverage marts by channel and schedule date

## Milestone 7 — Analytics product

- [ ] Rank transparent daily highlights
- [ ] Build archive search and pipeline-status views in Streamlit
