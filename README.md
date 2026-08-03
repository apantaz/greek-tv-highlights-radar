# Greek TV Highlights Radar & Archive

An end-to-end data project that collects fragmented Greek television schedules,
preserves their source observations, and builds toward a searchable archive and
explainable daily highlights.

## Current milestone

Version `v0.3.0` completed reliable multi-channel ingestion from
[ProgrammaTileorasis.gr](https://programmatileorasis.gr/). The source catalog is
discovered at runtime, each channel receives an isolated ingestion run, and partial
batch failures remain visible without preventing other channels from completing.

The current delivery completes the planned `v0.4.0` analytics warehouse. A channel
dimension, current-broadcast fact, and daily schedule mart turn the deterministic
current schedule into documented business-facing tables. The complete dbt graph now
contains seven models protected by 104 data tests.

```text
ProgrammaTileorasis.gr
  → ingestion run
  → immutable raw snapshot
  → typed parser and quality checks
  → append-only observations
  → current schedule view
  → documented dbt source boundary
  → tested raw dbt views
  → latest successful runs and current broadcasts
  → channel dimension, broadcast fact, and daily schedule mart
```

The current source adapter discovers the free channels advertised by the upstream
source at runtime and can ingest the complete catalog with isolated per-channel
failures. dbt transformations, TMDB enrichment, recommendations, and Streamlit follow
now that the ingestion boundary is reliable.

## Quick start

Python 3.12 or newer is required.

```bash
make install
make check
greek-tv ingest --channel ert1 --date 2026-07-19
```

List the currently available channels, then ingest one by its slug, source ID, or
display name:

```bash
greek-tv channels
```

For example:

```bash
greek-tv ingest --channel alpha --date 2026-07-19
```

Ingest every channel currently advertised by the source:

```bash
greek-tv ingest-all --date 2026-07-19
```

Batch ingestion discovers the catalog once and processes channels sequentially. One
failed channel does not stop the remaining schedules, and the command prints a final
success/failure summary. It exits with status `1` if any channel failed, making
partial failures visible to schedulers and CI.

## dbt warehouse

The repository includes a local dbt project configured for the same DuckDB database.
It requires dbt Core `1.12.x`; both local development dependencies and isolated Git
hooks enforce that compatibility line. The `version` in `dbt_project.yml` describes
the project itself, while `require-dbt-version` constrains the dbt Core runtime.
The ingestion tables are declared as documented dbt sources, establishing the
read-only boundary between Python ingestion and SQL transformation. Tested raw views
and intermediate current-state views feed three tables in `greek_tv_marts` without
changing source data.

Run dbt directly from its project directory:

```bash
cd dbt
dbt deps
dbt debug
dbt parse
dbt compile
dbt docs generate
```

dbt automatically uses the `profiles.yml` beside `dbt_project.yml`, so no global
profile or environment setup is required. Set `DBT_DUCKDB_PATH` to transform a
different database file. Close DBeaver and the DuckDB CLI before commands that write
models to avoid file-lock conflicts. See the [dbt project guide](dbt/README.md).

`make install` also installs Git hooks. Before each commit, pre-commit checks file
hygiene, malformed configuration, merge markers, private keys, Python lint, and
formatting. Commitizen validates commit messages against Conventional Commits. Before
each push, dbt-checkpoint validates parsing, compilation, and documentation generation,
then the full Python test suite runs.

Run the same gates manually:

```bash
make pre-commit
make pre-push
```

Commit messages use `<type>[optional scope]: <description>`, for example:

```text
feat: add ERT1 schedule ingestion
fix(parser): handle schedules crossing midnight
chore: configure pre-commit hooks
docs: document local setup
```

Run `cz commit` for an interactive prompt, or continue using `git commit` normally;
the `commit-msg` hook rejects messages that do not follow the convention.

Direct commits on `main` and `master` are blocked by `no-commit-to-branch`. The
pre-push guard also blocks any push whose remote destination is one of those protected
branches. Create a feature branch and merge it through a pull request:

```bash
git switch -c feat/my-change
git push -u origin feat/my-change
```

For server-side enforcement that cannot be bypassed with `--no-verify`, enable a
GitHub branch protection rule requiring pull requests for `main`.

By default, the command writes source snapshots under `data/raw/` and records runs and
broadcast observations in `data/greek_tv.duckdb`. Override these locations with
`RAW_DATA_DIR` and `DUCKDB_PATH`. Reliability settings are configurable through
`HTTP_TIMEOUT_SECONDS`, `HTTP_MAX_ATTEMPTS`, and `MINIMUM_SCHEDULE_RECORDS`.

Useful DuckDB relations:

```sql
select
    run_id,
    channel,
    schedule_date,
    status,
    records_parsed,
    error_message
from ingestion_runs
order by started_at desc;

select
    channel,
    starts_at,
    ends_at,
    title
from current_broadcasts
order by starts_at;
```

## Engineering properties

- Source-specific parsing is isolated behind a small adapter.
- Typed channel discovery separates stable CLI aliases from source identifiers and names.
- Batch ingestion isolates channel failures and returns a machine-visible partial-failure status.
- Every attempted ingestion has auditable success or failure metadata.
- Raw snapshots and parsed observations are immutable and run-addressed.
- The current schedule is derived from the latest successful run rather than updated in place.
- Athens-aware timestamps handle programmes that cross midnight.
- Existing milestone-one databases migrate non-destructively on first use.
- Bounded retries handle transient HTTP failures without retrying permanent client errors.
- Quality checks reject undersized, duplicate, and non-chronological schedules.
- Parser tests use offline HTML fixtures rather than a live website.
- Repository-local dbt configuration documents a read-only source boundary and needs
  no user-specific profile.
- dbt-checkpoint validates parsing, compilation, and documentation generation before
  pushes.
- The raw warehouse layer has explicit columns, persisted documentation, and 23 data
  tests covering its key source contracts.
- The intermediate layer derives current state deterministically and adds 29 tests
  for grain, lineage, required attributes, and temporal validity.
- The mart layer exposes Athens-local schedule analytics through a channel dimension,
  programme fact, and daily summary protected by 52 additional tests.
- CI runs Ruff, pytest, and dbt foundation validation on every pull request and push
  to `main`.

## Scope and limitations

Schedule data remains attributable to its source and ingestion run. The scraper
discovers the free-channel catalog exposed in the upstream `.channels_list` element.
Known channels receive readable stable aliases; newly advertised channels remain
immediately addressable by source ID or a `channel-<id>` fallback slug. The upstream
HTML is an external contract and may change; structural and quality failures are
recorded and fail loudly rather than silently storing incomplete data.

See the [data model and ERD](docs/data-model.md),
[architecture](docs/architecture.md), [decisions](docs/decisions.md), and the
[roadmap](docs/roadmap.md) for design context.
