# Data model

This diagram documents the current DuckDB ingestion model. It is intentionally
small: ingestion attempts are stored separately from the schedule rows observed by
each attempt.

```mermaid
erDiagram
    ingestion_runs ||--o{ broadcast_observations : produces

    ingestion_runs {
        varchar run_id PK
        varchar source
        varchar channel
        date schedule_date
        varchar source_url
        timestamptz started_at
        timestamptz completed_at
        varchar status
        integer records_parsed
        varchar snapshot_path
        varchar error_message
    }

    broadcast_observations {
        varchar observation_id PK
        varchar run_id FK
        varchar broadcast_id
        varchar channel
        varchar title
        timestamptz starts_at
        timestamptz ends_at
        varchar description
        varchar source_url
        timestamptz retrieved_at
    }
```

## Relationship

One row in `ingestion_runs` represents one ingestion attempt for a source, channel,
and requested schedule date. A successful run can produce many rows in
`broadcast_observations`; a failed or still-running attempt can have none.

The database enforces the relationship through
`broadcast_observations.run_id -> ingestion_runs.run_id`.

## Consumer view

`current_broadcasts` is a view rather than a physical table. It selects observations
from the latest successful run for each source, channel, and schedule date:

```mermaid
flowchart LR
    runs[ingestion_runs] -->|latest successful run| current[current_broadcasts view]
    observations[broadcast_observations] -->|matching run_id| current
```

The view deliberately excludes failed attempts and older successful observations,
while the underlying tables retain the complete ingestion history.

## dbt source boundary

The repository-local dbt project declares `ingestion_runs` and
`broadcast_observations` as documented sources in DuckDB's `main` schema. Derived
models never mutate these ingestion-owned tables.

The first derived layer adds two views without changing the source relationships:

```mermaid
flowchart LR
    runs[main.ingestion_runs] --> raw_runs[greek_tv_raw.raw_ingestion_runs]
    observations[main.broadcast_observations] --> raw_observations[greek_tv_raw.raw_broadcast_observations]
    raw_runs -->|run_id relationship test| raw_observations
```

Both views preserve their source grain. dbt tests enforce unique primary identifiers,
the run-to-observation relationship, required attributes, valid run statuses, and
basic numerical and temporal expectations.

## Enrichment cache

```mermaid
erDiagram
    tmdb_searches ||--o{ tmdb_candidates : returns
    tmdb_searches ||--o{ tmdb_lookup_contexts : supports
    tmdb_lookup_contexts ||--o{ tmdb_resolutions : evaluated_by
    tmdb_resolutions ||--o{ tmdb_candidate_scores : contains

    tmdb_searches {
        varchar search_id PK
        varchar normalized_title
        varchar search_query
        varchar language
        timestamptz retrieved_at
        json response_json
    }

    tmdb_candidates {
        varchar search_id PK, FK
        integer candidate_rank PK
        integer tmdb_id
        varchar media_type
        varchar title
        varchar original_title
        varchar original_language
        date release_date
        varchar overview
        double popularity
        double vote_average
        integer vote_count
    }

    tmdb_lookup_contexts {
        varchar lookup_id PK
        varchar source_title
        varchar normalized_source_title
        integer production_year
        json query_titles_json
        boolean used_query_override
        varchar search_id FK
        timestamptz created_at
    }

    tmdb_resolutions {
        varchar resolution_id PK
        varchar lookup_id FK
        varchar scoring_version
        varchar status
        varchar reason
        integer winning_candidate_rank
        integer tmdb_id
        varchar media_type
        double winning_score
        double runner_up_score
        double score_margin
        timestamptz resolved_at
    }

    tmdb_candidate_scores {
        varchar resolution_id PK, FK
        integer candidate_rank PK
        integer tmdb_id
        double title_score
        double year_score
        double total_score
        integer score_rank
    }
```

One `tmdb_searches` row preserves one complete external response. Its zero or more
`tmdb_candidates` rows contain only movie and TV results. The composite candidate key
preserves API response order without claiming that any candidate is the correct
programme match. `tmdb_lookup_contexts` separately preserves the source title,
production year, query variants, and selected search so reusable API cache entries do
not lose observation-specific evidence. dbt declares all three relations as read-only
enrichment sources. Each lookup can have append-only versioned resolution runs;
component scores preserve how every candidate received its final rank.

## Intermediate current-state lineage

```mermaid
flowchart LR
    raw_runs[greek_tv_raw.raw_ingestion_runs] --> latest[greek_tv_intermediate.int_latest_successful_ingestion_runs]
    raw_observations[greek_tv_raw.raw_broadcast_observations] --> current[greek_tv_intermediate.int_current_broadcasts]
    latest -->|selected run_id| current
```

`int_latest_successful_ingestion_runs` has one row per source, channel, and schedule
date. `int_current_broadcasts` retains only observations belonging to those runs. The
derived result is semantically equivalent to the ingestion-owned `current_broadcasts`
view while exposing additional source, schedule-date, observation, and completion
metadata for downstream models.

## Mart lineage

```mermaid
flowchart LR
    current[greek_tv_intermediate.int_current_broadcasts] --> channels[greek_tv_marts.dim_channels]
    current --> facts[greek_tv_marts.fct_current_broadcasts]
    channels -->|channel_key| facts
    facts --> daily[greek_tv_marts.mart_daily_channel_schedule]
```

`dim_channels` has one row per source and channel. `fct_current_broadcasts` has one
row per current programme observation and adds Athens-local dates, timestamps,
duration, midnight behavior, and schedule position. The daily mart aggregates the
fact to one source, channel, and requested schedule date.

## Legacy table

Databases created before the append-only model may also contain `broadcasts`. That
table is preserved for audit compatibility and migrated non-destructively into the
current model. It is not connected by a foreign key and is not part of the active
write path.
