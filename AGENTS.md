# AGENTS.md

# Greek TV Highlights Radar

## Overview

Greek TV Highlights Radar & Archive is a local-first Analytics Engineering project that builds a historical warehouse of Greek television programming.

The implemented platform currently:

1. Scrapes Greek TV schedules from public sources.
2. Discovers available channels dynamically.
3. Stores immutable raw snapshots and observations in DuckDB.
4. Preserves ingestion history for future analysis.
5. Declares the ingestion boundary as documented dbt sources.
6. Builds tested raw, intermediate, dimensional, fact, and mart models.
7. Retrieves, caches, and conservatively resolves TMDB candidates from explicit
   schedule evidence.
8. Enriches distinct current programmes in an idempotent, failure-isolated batch.
9. Retrieves and caches full metadata only for confidently matched TMDB identities.
10. Preserves mutable TMDB popularity and voting metrics as bounded historical snapshots.
11. Persists direct lineage from broadcast observations to enrichment lookups.
12. Publishes confidently matched TMDB identities as a canonical programme dimension.
13. Connects current broadcasts to nullable canonical programme identity.
14. Publishes mutable TMDB popularity and voting history as an analytical fact.
15. Measures enrichment coverage by channel and schedule date.
16. Ranks daily highlights both within channels and across all available channels
    through a versioned and decomposable scoring policy.
17. Presents daily highlights and their ranking evidence through a read-only
    Streamlit application.
18. Displays TMDB poster assets with an offline fallback and explicit attribution.
19. Offers Athens-aware upcoming viewing horizons and validated IMDb detail links.

The roadmap next expands the Streamlit application with archive search, programme
details, enrichment coverage, and pipeline status.

The project is intentionally designed as a production-quality portfolio that demonstrates modern Analytics Engineering and Data Engineering practices.

---

# Project Principles

When contributing to this repository, always prioritize:

- Correctness over speed.
- Readability over cleverness.
- Simplicity over unnecessary abstraction.
- Maintainability over short-term convenience.
- Reproducibility over manual processes.

Every change should make the project easier to understand and maintain.

---

# Technology Stack

Current stack:

- Python 3.12
- httpx
- BeautifulSoup
- DuckDB
- dbt Core 1.12
- dbt-duckdb 1.10
- pytest and pytest-cov
- Ruff
- pre-commit and Commitizen
- dbt-checkpoint
- Streamlit
- GitHub Actions

Planned additions:

- SQLFluff

---

# Architecture

The expected high-level pipeline is:

```
Public TV Schedule
        │
        ▼
   Python Scraper
        │
        ▼
     Raw Dataset
        │
        ▼
      DuckDB
        │
        ▼
      dbt Models
        │
        ▼
 Analytics Tables
        │
        ▼
   Streamlit App
```

Every stage should be deterministic and repeatable.

---

# Data Philosophy

Raw data is immutable.

Transformations should never overwrite raw datasets.

Preferred layers:

```
raw
    ↓
intermediate
    ↓
marts
```

Historical records should be preserved whenever possible.

Avoid destructive updates unless absolutely necessary.

---

# Python Guidelines

- Follow PEP 8.
- Use type hints.
- Prefer pathlib over os.path.
- Keep functions small.
- Avoid global state.
- Prefer composition over inheritance.
- Raise meaningful exceptions.
- Document public functions.

---

# SQL Guidelines

- Use lowercase SQL.
- Never use `select *`.
- Use explicit column names.
- Prefer CTEs for readability.
- Document complex business logic.
- Keep models focused on a single responsibility.

---

# dbt Guidelines

Every model should:

- Have a clear description.
- Have a single responsibility.
- Include tests whenever practical.
- Avoid unnecessary incremental logic.
- Favor readability over optimization.

Optimization should only happen after correctness has been achieved.

---

# Documentation Standards

Code should be self-explanatory whenever possible.

For non-trivial modules include:

- Purpose
- Inputs
- Outputs
- Assumptions
- Limitations

README files should remain beginner-friendly.

---

# Repository Structure

```
src/greek_tv/
dbt/
data/
tests/
docs/
.github/workflows/
```

Each folder should contain a single responsibility.

---

# Performance Philosophy

Do not optimize prematurely.

Priority order:

1. Correctness
2. Readability
3. Maintainability
4. Performance

Only optimize after measuring bottlenecks.

---

# AI Agent Responsibilities

AI agents are encouraged to:

- Improve documentation.
- Improve readability.
- Simplify implementations.
- Detect bugs.
- Suggest better architecture.
- Add tests.
- Explain trade-offs.
- Reduce duplication.
- Improve maintainability.

When multiple valid solutions exist, choose the one that best represents production-quality software engineering.

---

# AI Agent Restrictions

Do NOT:

- Rewrite large portions of the project without justification.
- Introduce unnecessary frameworks.
- Over-engineer simple solutions.
- Change repository structure without discussion.
- Remove business logic comments.
- Add dependencies without clear value.
- Replace stable code solely for stylistic reasons.

---

# Coding Philosophy

Assume this project may eventually become a real production application.

Write code that another engineer can understand six months from now.

Whenever possible, prefer explicit code over implicit behavior.

---

# Vision

The long-term vision is to build a complete local Analytics Engineering platform for Greek television programming.

The project should eventually demonstrate:

- Data ingestion
- Data warehousing
- Data modeling
- Data quality
- Metadata enrichment
- Historical archiving
- Analytics
- Interactive dashboards
- Testing
- CI/CD
- Documentation
- Production engineering practices

Every contribution should move the project toward that vision.

---

# Repository Philosophy

This repository exists primarily as a professional portfolio.

When proposing changes, always prefer solutions that showcase high-quality Analytics Engineering practices rather than simply making the code work.

The repository should demonstrate:

- Clean architecture
- Well-documented code
- Reproducible pipelines
- Professional engineering standards
- Production-ready thinking

The goal is not only to build a useful application, but also to showcase engineering quality to future collaborators and employers.
