"""Typed TMDB candidate and matched-entity retrieval."""

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

import httpx

TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/multi"
TMDB_API_ROOT = "https://api.themoviedb.org/3"
TMDB_AUTHENTICATION_URL = f"{TMDB_API_ROOT}/authentication"
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


@dataclass(frozen=True, slots=True)
class TmdbEntityDetails:
    """Stable metadata parsed from one matched movie or television entity."""

    tmdb_id: int
    media_type: str
    language: str
    title: str
    original_title: str
    original_language: str | None
    release_date: date | None
    overview: str | None
    tagline: str | None
    runtime_minutes: int | None
    status: str | None
    homepage: str | None
    imdb_id: str | None
    poster_path: str | None
    genres: tuple[str, ...]
    production_countries: tuple[str, ...]
    production_companies: tuple[str, ...]
    spoken_languages: tuple[str, ...]
    popularity: float | None
    vote_average: float | None
    vote_count: int | None
    payload: dict


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

    def validate_access_token(self) -> None:
        """Validate the configured read-access token without retrieving domain data."""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "User-Agent": "greek-tv-highlights-radar/0.6 (+public research project)",
        }
        with httpx.Client(
            timeout=self.timeout,
            headers=headers,
            transport=self.transport,
        ) as client:
            response = client.get(TMDB_AUTHENTICATION_URL)
            response.raise_for_status()

    def search(self, query: str, language: str = "el-GR") -> TmdbSearchResponse:
        """Return movie and TV candidates for a non-blank normalized title."""
        query = " ".join(query.split())
        if not query:
            raise ValueError("TMDB search query must not be blank")

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "User-Agent": "greek-tv-highlights-radar/0.6 (+public research project)",
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

    def details(
        self,
        media_type: str,
        tmdb_id: int,
        language: str = "el-GR",
    ) -> TmdbEntityDetails:
        """Retrieve stable details for one confidently matched movie or TV entity."""
        if media_type not in {"movie", "tv"}:
            raise ValueError("TMDB media type must be 'movie' or 'tv'")
        if tmdb_id < 1:
            raise ValueError("TMDB ID must be positive")
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "User-Agent": "greek-tv-highlights-radar/0.6 (+public research project)",
        }
        params = {"language": language, "append_to_response": "external_ids"}
        url = f"{TMDB_API_ROOT}/{media_type}/{tmdb_id}"
        with httpx.Client(
            timeout=self.timeout,
            headers=headers,
            transport=self.transport,
        ) as client:
            for attempt in range(1, self.max_attempts + 1):
                try:
                    response = client.get(url, params=params)
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
                if not isinstance(payload, dict):
                    raise ValueError("TMDB details response must be an object")
                return _parse_entity_details(payload, media_type, language, tmdb_id)
        raise RuntimeError("TMDB details retrieval exhausted without a response")

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


def _parse_entity_details(
    payload: dict,
    media_type: str,
    language: str,
    expected_tmdb_id: int,
) -> TmdbEntityDetails:
    tmdb_id = payload.get("id")
    title_key = "title" if media_type == "movie" else "name"
    original_title_key = "original_title" if media_type == "movie" else "original_name"
    release_date_key = "release_date" if media_type == "movie" else "first_air_date"
    title = _optional_text(payload.get(title_key))
    if tmdb_id != expected_tmdb_id or title is None:
        raise ValueError("TMDB details response has an invalid identity")
    runtime = payload.get("runtime")
    if media_type == "tv":
        episode_runtimes = payload.get("episode_run_time")
        runtime = (
            episode_runtimes[0] if isinstance(episode_runtimes, list) and episode_runtimes else None
        )
    external_ids = payload.get("external_ids")
    external_imdb_id = external_ids.get("imdb_id") if isinstance(external_ids, dict) else None
    return TmdbEntityDetails(
        tmdb_id=tmdb_id,
        media_type=media_type,
        language=language,
        title=title,
        original_title=_optional_text(payload.get(original_title_key)) or title,
        original_language=_optional_text(payload.get("original_language")),
        release_date=_optional_date(payload.get(release_date_key)),
        overview=_optional_text(payload.get("overview")),
        tagline=_optional_text(payload.get("tagline")),
        runtime_minutes=_optional_int(runtime),
        status=_optional_text(payload.get("status")),
        homepage=_optional_text(payload.get("homepage")),
        imdb_id=_optional_text(payload.get("imdb_id")) or _optional_text(external_imdb_id),
        poster_path=_optional_text(payload.get("poster_path")),
        genres=_named_values(payload.get("genres"), "name"),
        production_countries=_named_values(payload.get("production_countries"), "iso_3166_1"),
        production_companies=_named_values(payload.get("production_companies"), "name"),
        spoken_languages=_named_values(payload.get("spoken_languages"), "iso_639_1"),
        popularity=_optional_float(payload.get("popularity")),
        vote_average=_optional_float(payload.get("vote_average")),
        vote_count=_optional_int(payload.get("vote_count")),
        payload=payload,
    )


def _named_values(value: object, key: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(
        text
        for item in value
        if isinstance(item, dict) and (text := _optional_text(item.get(key))) is not None
    )


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
