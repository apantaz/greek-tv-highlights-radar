# Greek TV Highlights Radar & Archive

An end-to-end data project that collects fragmented Greek television schedules,
preserves their source observations, and builds toward a searchable archive and
explainable daily highlights.

## Current milestone

Version `v0.1.0` delivered the first vertical slice for one day of ERT1 programming from
[ProgrammaTileorasis.gr](https://programmatileorasis.gr/), saves the raw HTML for
reprocessing, validates parsed broadcasts with Pydantic, and upserts them into DuckDB.

The current delivery adds reliable, auditable ingestion. Every attempt is recorded,
raw snapshots and parsed observations are append-only, transient requests are retried,
and a `current_broadcasts` view exposes only the latest successful schedule per
channel and date.

```text
ProgrammaTileorasis.gr
  → ingestion run
  → immutable raw snapshot
  → typed parser and quality checks
  → append-only observations
  → current schedule view
```

The current source adapter discovers the free channels advertised by the upstream
source at runtime. Batch orchestration comes next; TMDB enrichment, dbt models,
recommendations, and Streamlit follow after the ingestion boundary is reliable.

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

`make install` also installs Git hooks. Before each commit, pre-commit checks file
hygiene, malformed configuration, merge markers, private keys, Python lint, and
formatting. Commitizen validates commit messages against Conventional Commits, and
before each push the full test suite runs.

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
- Every attempted ingestion has auditable success or failure metadata.
- Raw snapshots and parsed observations are immutable and run-addressed.
- The current schedule is derived from the latest successful run rather than updated in place.
- Athens-aware timestamps handle programmes that cross midnight.
- Existing milestone-one databases migrate non-destructively on first use.
- Bounded retries handle transient HTTP failures without retrying permanent client errors.
- Quality checks reject undersized, duplicate, and non-chronological schedules.
- Parser tests use offline HTML fixtures rather than a live website.
- CI runs Ruff and pytest on every pull request and push to `main`.

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
