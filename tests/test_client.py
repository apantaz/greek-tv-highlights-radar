from datetime import date

import httpx
import pytest

from greek_tv.scraper.channels import Channel
from greek_tv.scraper.client import ScheduleClient, save_snapshot


@pytest.mark.parametrize(
    ("channel", "expected_path"),
    [
        ("ert1", "18/%CE%95%CE%A1%CE%A41"),
        ("ert2", "87/%CE%95%CE%A1%CE%A42"),
        ("ert3", "6/%CE%95%CE%A1%CE%A43"),
        ("alpha", "5/ALPHA"),
        ("star", "3/STAR"),
        ("skai", "7/%CE%A3%CE%9A%CE%91%CE%AA"),
        ("open", "99/Open%20Beyond"),
        ("ert-news", "129/%CE%95%CE%A1%CE%A4%20News"),
    ],
)
def test_builds_date_addressable_channel_url(channel, expected_path):
    source_id, display_name = {
        "alpha": (5, "ALPHA"),
        "ert-news": (129, "ΕΡΤ News"),
        "ert1": (18, "ΕΡΤ1"),
        "ert2": (87, "ΕΡΤ2"),
        "ert3": (6, "ΕΡΤ3"),
        "open": (99, "Open Beyond"),
        "skai": (7, "ΣΚΑΪ"),
        "star": (3, "STAR"),
    }[channel]
    definition = Channel(channel, source_id, display_name)

    url = ScheduleClient().source_url(definition, date(2026, 7, 19))

    assert url == f"https://programmatileorasis.gr/free/{expected_path}?date=2026-07-19"


def test_fetches_and_parses_channel_catalog(channel_catalog_html):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, text=channel_catalog_html)

    channels = ScheduleClient(transport=httpx.MockTransport(handler)).fetch_catalog()

    assert len(channels) == 18


def test_saves_run_addressed_snapshot_without_overwrite(tmp_path):
    path = save_snapshot(
        "<html>ΕΡΤ1</html>",
        tmp_path,
        "ert1",
        date(2026, 7, 19),
        "run-123",
    )

    assert path == (tmp_path / "programmatileorasis" / "ert1" / "2026-07-19" / "run-123.html")
    assert path.read_text(encoding="utf-8") == "<html>ΕΡΤ1</html>"
    with pytest.raises(FileExistsError):
        save_snapshot("changed", tmp_path, "ert1", date(2026, 7, 19), "run-123")


def test_retries_transient_responses_with_bounded_backoff():
    attempts = 0
    delays = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        status = 503 if attempts < 3 else 200
        return httpx.Response(status, request=request, text="schedule")

    client = ScheduleClient(
        max_attempts=3,
        backoff_seconds=0.25,
        transport=httpx.MockTransport(handler),
        sleep=delays.append,
    )

    html, _ = client.fetch(Channel("ert1", 18, "ΕΡΤ1"), date(2026, 7, 19))

    assert html == "schedule"
    assert attempts == 3
    assert delays == [0.25, 0.5]


def test_does_not_retry_permanent_client_error():
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(404, request=request)

    client = ScheduleClient(
        transport=httpx.MockTransport(handler),
        sleep=lambda _: pytest.fail("a permanent error must not be retried"),
    )

    with pytest.raises(httpx.HTTPStatusError):
        client.fetch(Channel("ert1", 18, "ΕΡΤ1"), date(2026, 7, 19))
    assert attempts == 1
