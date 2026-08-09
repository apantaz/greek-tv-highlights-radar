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

The application uses `data/greek_tv.duckdb` and presents the top programmes across the
selected dynamically discovered channels. The fixed left navigation rail provides
individual channel checkboxes plus select-all and clear-all actions. Every card identifies
its broadcast channel and clearly separates the ranking Pick Score from the
schedule-to-TMDB Match Confidence. Channel logo URLs are parsed from the same live
source catalog and cached for one hour. Every logo uses an identical fixed-size,
`object-fit: contain` frame; unavailable images degrade to a neutral placeholder.
Ranking evidence remains visible. Results use a responsive four-column
grid on desktop, two columns on tablet, and one on mobile, with identical landscape poster
frames. Poster images are
non-interactive and cannot expand into a full-screen viewer. Missing posters use a
local placeholder; available posters are loaded from TMDB's documented `w500` image
service without making another API request. TMDB ratings use a gold star and remain
visually distinct from the project's highlight score.

The presentation uses a deliberate product interface rather than Streamlit's default
dashboard components: a branded discovery header, compact sidebar navigation,
editorial cards, rank and channel badges, a summary strip, and visual evidence bars.
The application remains server-rendered and read-only; the styling does not move
ranking logic or warehouse definitions into the browser.

Viewing horizons are evaluated using `Europe/Athens`: **Tonight**, **Tomorrow**, and
**Next 3 days** provide fast schedule navigation, while the calendar exposes dates
from the beginning of the available archive through yesterday. Today and future dates
are intentionally excluded from archive selection because schedules may still change.
Multi-day results remain grouped and independently ranked per day.
Each date presents four deliberately compact top picks. A card with a valid
TMDB-supplied `tt...` identifier is fully clickable and
opens the corresponding IMDb title page in a new tab; missing or malformed identifiers
produce a visibly unavailable, non-clickable card.

The **About & credits** section contains the approved TMDB logo and required notice:
"This product uses the TMDB API but is not endorsed or certified by TMDB." Ratings in
the cards are explicitly labeled as TMDB ratings; the available IMDb identifier is an
identity link and must not be presented as an IMDb rating.

Streamlit caches read results for at most 60 seconds and also invalidates them when
the database file changes.

Planned follow-up views include:

- archive search and channel/date filters;
- programme details backed by confidently resolved metadata;
- matched and unresolved enrichment coverage; and
- ingestion and enrichment pipeline status.
