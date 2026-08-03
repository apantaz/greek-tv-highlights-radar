# dbt warehouse

This directory contains the repository-local dbt project for transforming ingestion
data in DuckDB. Both the project and profile are version-controlled so contributors
do not need a user-specific `~/.dbt/profiles.yml`.

The project requires dbt Core `>=1.12.0,<1.13.0`. This constraint is declared through
`require-dbt-version` and mirrored in the development and pre-commit dependencies.
The separate `version` property is dbt project metadata and does not select the dbt
Core runtime.

The project declares two ingestion relations and eight enrichment relations as dbt
sources. The current graph projects all ten sources into tested raw views, derives
latest schedule and enrichment state through intermediate views, and publishes a
channel dimension, canonical programme dimension, current-broadcast fact, and daily
schedule mart. Programme-aware broadcast and historical metric facts are the next
warehouse deliveries.

The development target uses `greek_tv` as its base schema. dbt combines that base
with each model folder's custom schema:

| Model folder | DuckDB schema |
| --- | --- |
| `models/raw` | `greek_tv_raw` |
| `models/intermediate` | `greek_tv_intermediate` |
| `models/marts` | `greek_tv_marts` |

Relation and column descriptions are persisted for every model. All Python-owned
ingestion and enrichment tables remain in `main`; only dbt-derived relations use the
schemas above.
Seeds use the `raw` custom schema, producing `greek_tv_raw`. Snapshots use the
`snapshots` target schema and default to the timestamp strategy; each snapshot must
still declare the column used by `updated_at`. Data tests do not persist failed rows
by default, while `test_failures` is reserved as their failure schema if persistence
is enabled later.

Reusable dbt documentation blocks live under `docs/raw`, `docs/intermediate`, and
`docs/marts`. Each layer separates table-level guidance in `tables.md` from
column-level guidance in `columns.md`. Each model and column description in
`models/raw/schema.yml` references its corresponding block with `{{ doc('...') }}`.

Enter the dbt project. dbt discovers the `profiles.yml` beside `dbt_project.yml`, so
no `DBT_PROFILES_DIR` export or user-specific profile is needed:

```bash
cd dbt
dbt debug
dbt parse
```

The same shell can run standard commands directly:

```bash
dbt build
dbt test
dbt compile
dbt docs generate
```

Install the pinned dbt packages after cloning or changing `packages.yml`:

```bash
dbt deps
```

The project includes dbt-expectations for richer data-quality assertions, dbt-utils
for reusable cross-database macros, codegen for development-time model scaffolding,
and dbt-date for calendar transformations. Package versions are pinned so local and
CI behavior remains reproducible.

By default, dbt connects to the repository's `data/greek_tv.duckdb`. Override the
database without editing project files:

```bash
DBT_DUCKDB_PATH=/absolute/path/to/database.duckdb dbt build
```

Disconnect DuckDB CLI, DBeaver, or other writers before running dbt because DuckDB
permits only one process to hold a write connection to a database file.

Build the raw layer and its source-boundary tests with:

```bash
dbt build --select path:models/raw
```

Build only enrichment-tagged raw models and their tests with:

```bash
dbt build --select +tag:enrichment
```

Build the intermediate layer together with its upstream raw dependencies:

```bash
dbt build --select +path:models/intermediate
```

Build the complete warehouse through the business-facing marts:

```bash
dbt build --select +path:models/marts
```

## Model tags

Layer tags are configured once in `dbt_project.yml`, while model-specific semantic
roles are declared in the relevant model config. Tags are additive: for example,
`fct_current_broadcasts` has both `marts` and `fact`.

| Tag | Scope |
| --- | --- |
| `raw` | Source-aligned raw models |
| `enrichment` | Models derived from TMDB enrichment sources |
| `intermediate` | Reusable transformation models |
| `marts` | Business-facing models |
| `dimension` | Dimension models |
| `fact` | Fact models |
| `aggregate` | Aggregated consumer marts |

Use tags as dbt selectors:

```bash
dbt build --select tag:raw
dbt build --select tag:intermediate
dbt build --select tag:marts
dbt build --select tag:fact
```

The pre-push hooks use dbt-checkpoint to parse the project, compile changed SQL
models, and generate the documentation catalog.
