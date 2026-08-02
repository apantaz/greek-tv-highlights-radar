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
