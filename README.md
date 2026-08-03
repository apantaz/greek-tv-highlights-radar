# Greek TV Highlights Radar & Archive

An end-to-end data project that collects fragmented Greek television schedules,
preserves their source observations, and builds toward a searchable archive and
explainable daily highlights.

## Current milestone

The `v0.6.0` release adds unattended batch enrichment and full metadata retrieval for
confidently matched TMDB entities. It builds on deterministic title evidence,
immutable candidate caching, conservative automatic resolution, and the analytics
warehouse backed by reliable multi-channel ingestion from
[ProgrammaTileorasis.gr](https://programmatileorasis.gr/). The source catalog is
discovered at runtime, ingestion history remains immutable, and dbt transforms the
latest successful schedules into documented business-facing tables.

The warehouse includes tested ingestion and enrichment raw views, schedule
intermediate views, a channel dimension, a current-broadcast fact, and a daily
schedule mart. The complete dbt graph contains 14 models protected by 191 data tests.

Current development projects all seven enrichment relations through a documented,
tested dbt raw boundary. The next delivery derives latest resolution, entity-detail,
and metric state through intermediate models. The Python suite contains 100 tests.

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

Current programme evidence
  → deterministic title and production-year extraction
  → cached TMDB movie and TV candidates
  → explainable candidate scores
  → matched identity or explicit unresolved outcome
  → cached full metadata for matched identities only
```

The source adapter discovers the free channels advertised by the upstream source at
runtime and can ingest the complete catalog with isolated per-channel failures. TMDB
enrichment preserves each source title, caches typed TMDB movie and TV candidates
with their raw API evidence, and scores them through a conservative, explainable
policy. Uncertain results remain unresolved. Recommendations and Streamlit follow now
that the ingestion, analytics, and external-metadata boundaries are reliable.

### TMDB candidate cache

Set a private TMDB API Read Access Token in your shell, then retrieve candidates for
one source title:

```bash
export TMDB_API_TOKEN="your-read-access-token"
greek-tv tmdb-check
```

A valid token prints `TMDB connection OK: read-access token is valid`. A missing,
invalid, or unreachable configuration exits with status `1` and a concise diagnostic
without writing to DuckDB. The command calls TMDB's dedicated authentication
validation endpoint, making it suitable for setup checks and fast debugging.

Then retrieve candidates for one source title:

```bash
greek-tv tmdb-search \
  --title "Ο Χάρι Πότερ (Harry Potter and the Order of the Phoenix)" \
  --description "Αμερικανικής παραγωγής 2007."
```

The command normalizes the title, searches TMDB for movie and TV results, and stores
the raw response plus every supported candidate in `data/greek_tv.duckdb`. It also
records a lookup context containing the source title, extracted production year,
ordered query variants, and selected search. Repeating the same title and language
uses the local cache without requiring the token or a network request. Use `--refresh`
to append a new retrieval, or `--language en-US` to request another response language.
Never commit the token; `.env` files are ignored.

The API query preserves accents and readable punctuation while the cache identity uses
the canonical normalized form. Parenthesized Latin titles are tried automatically
before the localized title, so source evidence can resolve without manual rewriting:

```bash
greek-tv tmdb-search \
  --title "Η Μάνα του 10αριού (La Mama del 10)" \
  --refresh
```

Some descriptions begin with a bracketed international title. Pass the source
description with `--description` when diagnosing one title. `--query` is available
for diagnostic experiments, but it is not part of unattended enrichment: records
whose source text contains insufficient evidence remain unresolved.

Candidate rank records API response order only. It is not an accepted entity match or
a recommendation score.

Every lookup is scored automatically after retrieval. Title similarity contributes
the full score when no production year is available; when a year is present, title
similarity contributes 75% and year agreement contributes 25%. A match requires at
least 85 points and a lead of at least 10 points over the runner-up. Anything weaker
or ambiguous is persisted as `unresolved` with a machine-readable reason and no human
review step. Unresolved rows keep their accepted TMDB identity fields null while the
candidate-score rows retain the evidence needed to explain the outcome.

Enrich every distinct programme represented by the current schedules without manual
title entry:

```bash
export TMDB_API_TOKEN="your-read-access-token"
greek-tv enrich
```

For a controlled first run, bound the number of distinct evidence combinations:

```bash
greek-tv enrich --limit 10
```

Target one ingested channel and requested schedule date:

```bash
greek-tv enrich --channel star --date 2026-08-01
```

Batch enrichment is sequential, reuses cached searches, skips evidence already scored
by the current policy version, and isolates title-level failures. The final summary
reports matched, unresolved, skipped, failed, cached, and retrieved counts. A repeated
run therefore performs no TMDB requests for unchanged processed evidence. The command
exits with status `1` only when operational failures occur; unresolved identities are
valid data outcomes. Channel matching is case-insensitive, and the date refers to the
requested ingestion schedule date rather than timestamps after midnight rollover.

Retrieve complete metadata for every confidently matched identity:

```bash
greek-tv enrich-entities
```

The command processes distinct accepted `(media_type, tmdb_id)` pairs and caches
results by identity and response language. It never retrieves details for unresolved
programmes. Repeated runs reuse the local cache without creating API requests; use
`--limit 10` for a controlled run, `--language en-US` for another response language,
or `--refresh` to append fresh source evidence. One failed identity does not stop the
remaining batch, and any operational failure produces exit status `1`.

Stable normalized columns include titles, overview, dates, runtime, genres,
production countries and companies, spoken languages, homepage, status, and the
IMDb ID supplied directly by TMDB. The complete response is retained for audit.
Mutable popularity and voting metrics are intentionally excluded from these stable
columns and stored as timestamped observations instead.

Snapshot metrics whose latest observation is at least 24 hours old:

```bash
greek-tv snapshot-metrics
```

Use `--max-age-hours 12` to change the refresh boundary, `--limit 10` for a controlled
run, or `--max-age-hours 0` to force a new observation. Fresh entities make no API
request, and a fully fresh run does not require the token. Each new details response
and its metric observation are committed atomically; failures remain isolated by
entity. Existing `v0.6.0` detail responses are backfilled non-destructively on first
use.

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
The ingestion and enrichment tables are declared as documented dbt sources,
establishing the read-only boundary between Python and SQL transformation. The
current dbt graph transforms ingestion sources through the complete schedule
warehouse and projects every enrichment source into a tested raw view. Enrichment
intermediate and mart models are the next warehouse deliveries.

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

select
    searches.normalized_title,
    candidates.candidate_rank,
    candidates.media_type,
    candidates.tmdb_id,
    candidates.title,
    candidates.release_date
from tmdb_searches as searches
inner join tmdb_candidates as candidates using (search_id)
order by searches.retrieved_at desc, candidates.candidate_rank;

select
    contexts.source_title,
    contexts.production_year,
    resolutions.status,
    resolutions.reason,
    resolutions.tmdb_id,
    resolutions.media_type,
    resolutions.winning_score,
    resolutions.score_margin
from tmdb_lookup_contexts as contexts
inner join tmdb_resolutions as resolutions using (lookup_id)
qualify row_number() over (
    partition by contexts.lookup_id
    order by resolutions.resolved_at desc
) = 1
order by contexts.created_at desc;

select
    media_type,
    tmdb_id,
    language,
    title,
    original_title,
    release_date,
    runtime_minutes,
    imdb_id,
    genres_json
from tmdb_entity_details
qualify row_number() over (
    partition by media_type, tmdb_id, language
    order by retrieved_at desc, entity_detail_id desc
) = 1
order by media_type, title;

select
    media_type,
    tmdb_id,
    popularity,
    vote_average,
    vote_count,
    observed_at
from tmdb_entity_metric_observations
order by media_type, tmdb_id, observed_at;
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
- The raw warehouse layer has explicit columns, persisted documentation, and 110 data
  tests covering ingestion and enrichment source contracts.
- The intermediate layer derives current state deterministically and adds 29 tests
  for grain, lineage, required attributes, and temporal validity.
- The mart layer exposes Athens-local schedule analytics through a channel dimension,
  programme fact, and daily summary protected by 52 additional tests.
- TMDB searches retain immutable raw responses and typed candidates without silently
  treating API response order as an accepted entity match.
- Versioned candidate scores make every matched or unresolved identity explainable.
- Batch enrichment is cache-aware, evidence-idempotent, filterable, and isolates
  programme-level failures.
- Full entity metadata is retrieved only for accepted matches and cached by stable
  TMDB identity and response language.
- Mutable TMDB popularity and voting metrics are preserved as bounded, append-only
  historical observations.
- CI runs Ruff, pytest, and dbt foundation validation on every pull request and push
  to `main`.

## Scope and limitations

Schedule data remains attributable to its source and ingestion run. The scraper
discovers the free-channel catalog exposed in the upstream `.channels_list` element.
Known channels receive readable stable aliases; newly advertised channels remain
immediately addressable by source ID or a `channel-<id>` fallback slug. The upstream
HTML is an external contract and may change; structural and quality failures are
recorded and fail loudly rather than silently storing incomplete data.

TMDB enrichment retains search responses, candidate metadata, scoring evidence,
conservative resolution outcomes, full details for accepted entities, and historical
popularity and voting observations. Credits are not fetched yet.

See the [data model and ERD](docs/data-model.md),
[architecture](docs/architecture.md), [decisions](docs/decisions.md), and the
[roadmap](docs/roadmap.md) for design context.

## Credits

Schedule data is collected from
[ProgrammaTileorasis.gr](https://programmatileorasis.gr/). External movie and
television metadata is supplied by [TMDB](https://www.themoviedb.org/).

This product uses the TMDB API but is not endorsed or certified by TMDB.
