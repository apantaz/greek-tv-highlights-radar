# Streamlit analytics app

The first application view consumes the tested `mart_daily_highlights` dbt mart. It
is a read-only presentation layer: it does not read ingestion tables, mutate DuckDB,
or call external APIs.

Build the mart and launch the app from the repository root:

```bash
cd dbt
dbt build --select +mart_daily_highlights
cd ..
streamlit run streamlit/app.py
```

The sidebar uses `data/greek_tv.duckdb` by default and accepts another local DuckDB
path. Select a source, channel, and archived schedule date to inspect the ranked
programmes, normalized score components, raw TMDB evidence, metric observation time,
and ranking-policy version.

Streamlit caches read results for at most 60 seconds and also invalidates them when
the database file changes. Use **Refresh data** to invalidate the cache immediately.

Planned follow-up views include:

- archive search and channel/date filters;
- programme details backed by confidently resolved metadata;
- matched and unresolved enrichment coverage; and
- ingestion and enrichment pipeline status.
