from datetime import UTC, date, datetime

import pytest

from greek_tv.scraper.parser import ScheduleParseError, parse_schedule

SOURCE_URL = "https://programmatileorasis.gr/free/18/ΕΡΤ1?date=2026-07-19"
RETRIEVED_AT = datetime(2026, 7, 19, 10, tzinfo=UTC)


def parse(html: str):
    return parse_schedule(
        html,
        channel_id=18,
        channel="ΕΡΤ1",
        schedule_date=date(2026, 7, 19),
        source_url=SOURCE_URL,
        retrieved_at=RETRIEVED_AT,
    )


def test_parses_programmes_and_preserves_greek(schedule_html):
    broadcasts = parse(schedule_html)

    assert len(broadcasts) == 3
    assert broadcasts[0].title == "Μουντιάλ 2026 | Τελικός"
    assert broadcasts[0].description == "Η μεγάλη ποδοσφαιρική βραδιά."
    assert broadcasts[-1].title == "Το Κοινωνικό Δίκτυο"
    assert broadcasts[-1].description is None


def test_rolls_early_morning_programmes_into_next_calendar_day(schedule_html):
    broadcasts = parse(schedule_html)

    assert broadcasts[0].starts_at.isoformat() == "2026-07-19T22:00:00+03:00"
    assert broadcasts[0].ends_at == broadcasts[1].starts_at
    assert broadcasts[1].starts_at.isoformat() == "2026-07-20T00:30:00+03:00"
    assert broadcasts[2].starts_at.isoformat() == "2026-07-20T02:00:00+03:00"
    assert broadcasts[2].ends_at is None


def test_rejects_missing_schedule_table():
    with pytest.raises(ScheduleParseError, match="channel18"):
        parse("<html></html>")
