# Architecture Decision Records

## ADR-001
DuckDB chosen for local analytical storage.

DuckDB keeps the portfolio project runnable without infrastructure while supporting
analytical SQL and a future dbt layer. A hosted, concurrent product would revisit
this decision.

## ADR-002
Raw source observations are preserved before parsing.

This enables parser debugging and future reprocessing without repeatedly requesting
the upstream site.

## ADR-003
The first release supports one source and one channel.

A narrow end-to-end slice demonstrates reliability and exposes real data problems
before abstractions for multiple sources are introduced.
