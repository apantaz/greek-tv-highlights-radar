"""HTTP access and immutable snapshot storage for TV schedules."""

import time
from collections.abc import Callable
from datetime import date
from pathlib import Path
from urllib.parse import quote

import httpx

from greek_tv.scraper.channels import Channel, parse_channel_catalog

BASE_URL = "https://programmatileorasis.gr"
SOURCE_NAME = "programmatileorasis"
RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


class ScheduleClient:
    """Fetch schedule pages with bounded retries for transient failures."""

    def __init__(
        self,
        timeout: float = 20.0,
        max_attempts: int = 3,
        backoff_seconds: float = 0.5,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.backoff_seconds = backoff_seconds
        self.transport = transport
        self.sleep = sleep

    def _get(self, url: str) -> tuple[str, str]:
        headers = {"User-Agent": "greek-tv-highlights-radar/0.2 (+public research project)"}
        with httpx.Client(
            timeout=self.timeout,
            follow_redirects=True,
            headers=headers,
            transport=self.transport,
        ) as client:
            for attempt in range(1, self.max_attempts + 1):
                try:
                    response = client.get(url)
                except httpx.TransportError:
                    if attempt == self.max_attempts:
                        raise
                    self.sleep(self.backoff_seconds * (2 ** (attempt - 1)))
                    continue

                if response.status_code in RETRYABLE_STATUS_CODES:
                    if attempt == self.max_attempts:
                        response.raise_for_status()
                    self.sleep(self.backoff_seconds * (2 ** (attempt - 1)))
                    continue

                response.raise_for_status()
                return response.text, str(response.url)
        raise RuntimeError("schedule fetch exhausted without a response")

    def fetch_catalog(self) -> tuple[Channel, ...]:
        """Fetch and parse the channel catalog currently advertised by the source."""
        html, _ = self._get(BASE_URL)
        return parse_channel_catalog(html)

    def source_url(self, channel: Channel, schedule_date: date) -> str:
        encoded_name = quote(channel.display_name, safe="")
        return (
            f"{BASE_URL}/free/{channel.source_id}/{encoded_name}?date={schedule_date.isoformat()}"
        )

    def fetch(self, channel: Channel, schedule_date: date) -> tuple[str, str]:
        """Fetch one page, retrying only transport and explicitly transient HTTP errors."""
        url = self.source_url(channel, schedule_date)
        return self._get(url)


def save_snapshot(
    html: str,
    raw_root: Path,
    channel: str,
    schedule_date: date,
    run_id: str,
) -> Path:
    """Write a run-addressed raw response without permitting overwrite."""
    destination = raw_root / SOURCE_NAME / channel.lower() / schedule_date.isoformat()
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / f"{run_id}.html"
    with path.open("x", encoding="utf-8") as snapshot:
        snapshot.write(html)
    return path
