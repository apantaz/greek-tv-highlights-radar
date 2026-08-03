"""Typed TMDB candidate retrieval without automatic entity selection."""

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

import httpx

TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/multi"
RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


@dataclass(frozen=True, slots=True)
class TmdbCandidate:
    """One movie or television candidate returned by TMDB."""

    rank: int
    tmdb_id: int
    media_type: str
    title: str
    original_title: str
    original_language: str | None
    release_date: date | None
    overview: str | None
    popularity: float | None
    vote_average: float | None
    vote_count: int | None


@dataclass(frozen=True, slots=True)
class TmdbSearchResponse:
    """The raw response and supported candidates from one TMDB search."""

    payload: dict
    candidates: tuple[TmdbCandidate, ...]


class TmdbClient:
    """Search TMDB with bearer authentication and bounded transient retries."""

    def __init__(
        self,
        access_token: str,
        timeout: float = 20.0,
        max_attempts: int = 3,
        backoff_seconds: float = 0.5,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not access_token.strip():
            raise ValueError("TMDB access token must not be blank")
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self.access_token = access_token
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.backoff_seconds = backoff_seconds
        self.transport = transport
        self.sleep = sleep

    def search(self, query: str, language: str = "el-GR") -> TmdbSearchResponse:
        """Return movie and TV candidates for a non-blank normalized title."""
        query = " ".join(query.split())
        if not query:
            raise ValueError("TMDB search query must not be blank")

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "User-Agent": "greek-tv-highlights-radar/0.4 (+public research project)",
        }
        params = {
            "query": query,
            "language": language,
            "include_adult": "false",
            "page": "1",
        }
        with httpx.Client(
            timeout=self.timeout,
            headers=headers,
            transport=self.transport,
        ) as client:
            for attempt in range(1, self.max_attempts + 1):
                try:
                    response = client.get(TMDB_SEARCH_URL, params=params)
                except httpx.TransportError:
                    if attempt == self.max_attempts:
                        raise
                    self._backoff(attempt)
                    continue

                if response.status_code in RETRYABLE_STATUS_CODES:
                    if attempt == self.max_attempts:
                        response.raise_for_status()
                    self._backoff(attempt)
                    continue

                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
                    raise ValueError("TMDB search response does not contain a results list")
                return TmdbSearchResponse(payload, _parse_candidates(payload["results"]))

        raise RuntimeError("TMDB search exhausted without a response")

    def _backoff(self, attempt: int) -> None:
        self.sleep(self.backoff_seconds * (2 ** (attempt - 1)))


def _parse_candidates(results: list) -> tuple[TmdbCandidate, ...]:
    candidates = []
    for item in results:
        if not isinstance(item, dict) or item.get("media_type") not in {"movie", "tv"}:
            continue
        media_type = item["media_type"]
        title_key = "title" if media_type == "movie" else "name"
        original_title_key = "original_title" if media_type == "movie" else "original_name"
        release_date_key = "release_date" if media_type == "movie" else "first_air_date"
        title = item.get(title_key)
        tmdb_id = item.get("id")
        if not isinstance(title, str) or not title.strip() or not isinstance(tmdb_id, int):
            continue
        candidates.append(
            TmdbCandidate(
                rank=len(candidates) + 1,
                tmdb_id=tmdb_id,
                media_type=media_type,
                title=title.strip(),
                original_title=_optional_text(item.get(original_title_key)) or title.strip(),
                original_language=_optional_text(item.get("original_language")),
                release_date=_optional_date(item.get(release_date_key)),
                overview=_optional_text(item.get("overview")),
                popularity=_optional_float(item.get("popularity")),
                vote_average=_optional_float(item.get("vote_average")),
                vote_count=_optional_int(item.get("vote_count")),
            )
        )
    return tuple(candidates)


def _optional_text(value: object) -> str | None:
    return value.strip() or None if isinstance(value, str) else None


def _optional_date(value: object) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _optional_float(value: object) -> float | None:
    return float(value) if isinstance(value, int | float) else None


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) else None
