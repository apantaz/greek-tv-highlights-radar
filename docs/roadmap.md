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

- Add representative commercial and public channels
- Add retries with bounded backoff and structured run metadata
- Detect upstream HTML changes and enforce data-quality thresholds
- Reconcile updated schedules without losing observation history

## Milestone 3 — Enrichment and entity resolution

- Normalize Greek and international titles
- Retrieve and cache TMDB candidates
- Score matches with explainable confidence and manual overrides

## Milestone 4 — Analytics and product

- Model staging and analytical layers with dbt
- Rank transparent daily highlights
- Build archive search and pipeline-status views in Streamlit
