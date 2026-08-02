from datetime import date

import httpx
import pytest

from greek_tv.scraper.client import ScheduleClient, save_snapshot


def test_builds_date_addressable_channel_url():
    url = ScheduleClient().source_url("ert1", date(2026, 7, 19))

    assert url == "https://programmatileorasis.gr/free/18/%CE%95%CE%A1%CE%A41?date=2026-07-19"


def test_rejects_unknown_channel():
    with pytest.raises(ValueError, match="unsupported channel"):
        ScheduleClient().source_url("unknown", date(2026, 7, 19))


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

    html, _ = client.fetch("ert1", date(2026, 7, 19))

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
        client.fetch("ert1", date(2026, 7, 19))
    assert attempts == 1
