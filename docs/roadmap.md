# Roadmap

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

## Milestone 3 — Analytics warehouse foundation

- [x] Configure a repository-local dbt-duckdb project
- [x] Declare ingestion relations as documented dbt sources
- [x] Add reproducible direct dbt commands and CI/pre-push validation
- [x] Add raw models and source-boundary tests
- [x] Add intermediate latest-successful-run logic
- [x] Add dimensional, fact, and initial mart models
- [x] Generate dbt documentation and lineage artifacts

## Milestone 4 — Enrichment and entity resolution

- [x] Normalize Greek and international titles deterministically
- [x] Retrieve and cache TMDB candidates with immutable raw responses
- [ ] Score matches with explainable confidence and manual overrides

## Milestone 5 — Analytics product

- [ ] Rank transparent daily highlights
- [ ] Build archive search and pipeline-status views in Streamlit
