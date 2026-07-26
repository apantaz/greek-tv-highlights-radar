import re
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup, Tag

from greek_tv.models import Broadcast

TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")
ATHENS = ZoneInfo("Europe/Athens")


class ScheduleParseError(ValueError):
    pass


def _row_text(row: Tag) -> tuple[str, str, str | None] | None:
    cells = row.find_all("td", recursive=False)
    if len(cells) != 2:
        return None
    time_text = cells[0].get_text(" ", strip=True)
    if not TIME_PATTERN.fullmatch(time_text):
        return None

    description_element = cells[1].select_one(".description")
    description = None
    if description_element:
        button = description_element.select_one(".buttony")
        if button:
            button.decompose()
        description = description_element.get_text(" ", strip=True) or None
        description_element.extract()

    title = cells[1].get_text(" ", strip=True)
    if not title:
        raise ScheduleParseError(f"missing title for programme at {time_text}")
    return time_text, title, description


def parse_schedule(
    html: str,
    *,
    channel_id: int,
    channel: str,
    schedule_date: date,
    source_url: str,
    retrieved_at: datetime | None = None,
) -> list[Broadcast]:
    retrieved_at = retrieved_at or datetime.now(UTC)
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one(f"table#channel{channel_id}")
    if table is None:
        raise ScheduleParseError(f"schedule table channel{channel_id} was not found")

    parsed_rows = [parsed for row in table.select("tbody tr") if (parsed := _row_text(row))]
    if not parsed_rows:
        raise ScheduleParseError("schedule contains no programme rows")

    starts: list[datetime] = []
    day_offset = 0
    previous_minutes: int | None = None
    for time_text, _, _ in parsed_rows:
        hour, minute = map(int, time_text.split(":"))
        minutes = hour * 60 + minute
        if previous_minutes is not None and minutes < previous_minutes:
            day_offset += 1
        starts.append(
            datetime.combine(
                schedule_date + timedelta(days=day_offset), datetime.min.time(), ATHENS
            )
            + timedelta(minutes=minutes)
        )
        previous_minutes = minutes

    return [
        Broadcast(
            channel=channel,
            title=title,
            starts_at=starts[index],
            ends_at=starts[index + 1] if index + 1 < len(starts) else None,
            description=description,
            source_url=source_url,
            retrieved_at=retrieved_at,
        )
        for index, (_, title, description) in enumerate(parsed_rows)
    ]
