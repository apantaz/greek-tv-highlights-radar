# Greek TV Highlights Radar & Archive

An end-to-end data project that collects fragmented Greek television schedules,
preserves their source observations, and builds toward a searchable archive and
explainable daily highlights.

## Current milestone

The first vertical slice ingests one day of ERT1 programming from
[ProgrammaTileorasis.gr](https://programmatileorasis.gr/), saves the raw HTML for
reprocessing, validates parsed broadcasts with Pydantic, and upserts them into DuckDB.

```text
ProgrammaTileorasis.gr → raw HTML snapshot → typed parser → DuckDB
```

The initial scope is deliberately narrow: one channel, one source adapter, and one
command. TMDB enrichment, dbt models, recommendations, and Streamlit come after the
ingestion boundary is reliable.

## Quick start

Python 3.12 or newer is required.

```bash
make install
make check
greek-tv ingest --channel ert1 --date 2026-07-19
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

By default, the command writes source snapshots under `data/raw/` and broadcasts to
`data/greek_tv.duckdb`. Override these locations with `RAW_DATA_DIR` and
`DUCKDB_PATH`.

## Engineering properties

- Source-specific parsing is isolated behind a small adapter.
- Raw observations are retained separately from normalized records.
- Athens-aware timestamps handle programmes that cross midnight.
- Stable broadcast identities make repeated ingestion idempotent.
- Parser tests use offline HTML fixtures rather than a live website.
- CI runs Ruff and pytest on every pull request and push to `main`.

## Scope and limitations

Schedule data remains attributable to its source through `source_url` and
`retrieved_at`. The scraper currently supports ERT1 only. The upstream HTML is an
external contract and may change; a missing schedule table fails loudly rather than
silently storing incomplete data.

See [architecture](docs/architecture.md), [decisions](docs/decisions.md), and the
[roadmap](docs/roadmap.md) for design context.
