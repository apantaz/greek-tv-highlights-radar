from datetime import date

import pytest

from greek_tv.scraper.client import ScheduleClient, save_snapshot


def test_builds_date_addressable_channel_url():
    url = ScheduleClient().source_url("ert1", date(2026, 7, 19))

    assert url == ("https://programmatileorasis.gr/free/18/%CE%95%CE%A1%CE%A41?date=2026-07-19")


def test_rejects_unknown_channel():
    with pytest.raises(ValueError, match="unsupported channel"):
        ScheduleClient().source_url("unknown", date(2026, 7, 19))


def test_saves_raw_snapshot(tmp_path):
    path = save_snapshot("<html>ΕΡΤ1</html>", tmp_path, "ert1", date(2026, 7, 19))

    assert path == tmp_path / "programmatileorasis" / "ert1" / "2026-07-19.html"
    assert path.read_text(encoding="utf-8") == "<html>ΕΡΤ1</html>"
