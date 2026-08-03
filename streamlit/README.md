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
and ranking-policy version. Results are displayed as poster cards. Missing posters use
a local placeholder; available posters are loaded from TMDB's documented `w500` image
service without making another API request.

The **About & credits** section contains the approved TMDB logo and required notice:
"This product uses the TMDB API but is not endorsed or certified by TMDB." Ratings in
the cards are explicitly labeled as TMDB ratings; the available IMDb identifier is an
identity link and must not be presented as an IMDb rating.

Streamlit caches read results for at most 60 seconds and also invalidates them when
the database file changes. Use **Refresh data** to invalidate the cache immediately.

Planned follow-up views include:

- archive search and channel/date filters;
- programme details backed by confidently resolved metadata;
- matched and unresolved enrichment coverage; and
- ingestion and enrichment pipeline status.
