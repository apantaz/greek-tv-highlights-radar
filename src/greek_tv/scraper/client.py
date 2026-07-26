from datetime import date
from pathlib import Path
from urllib.parse import quote

import httpx

BASE_URL = "https://programmatileorasis.gr"
CHANNELS = {"ert1": (18, "ΕΡΤ1")}


class ScheduleClient:
    def __init__(self, timeout: float = 20.0) -> None:
        self.timeout = timeout

    def source_url(self, channel: str, schedule_date: date) -> str:
        try:
            channel_id, channel_name = CHANNELS[channel.lower()]
        except KeyError as error:
            supported = ", ".join(sorted(CHANNELS))
            raise ValueError(f"unsupported channel {channel!r}; choose one of: {supported}") from error
        encoded_name = quote(channel_name, safe="")
        return f"{BASE_URL}/free/{channel_id}/{encoded_name}?date={schedule_date.isoformat()}"

    def fetch(self, channel: str, schedule_date: date) -> tuple[str, str]:
        url = self.source_url(channel, schedule_date)
        headers = {"User-Agent": "greek-tv-highlights-radar/0.1 (+public research project)"}
        with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=headers) as client:
            response = client.get(url)
            response.raise_for_status()
        return response.text, str(response.url)


def save_snapshot(html: str, raw_root: Path, channel: str, schedule_date: date) -> Path:
    destination = raw_root / "programmatileorasis" / channel.lower()
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / f"{schedule_date.isoformat()}.html"
    path.write_text(html, encoding="utf-8")
    return path
