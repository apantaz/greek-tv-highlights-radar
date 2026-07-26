from datetime import UTC, date, datetime
from pathlib import Path

from greek_tv.database import BroadcastRepository
from greek_tv.scraper.client import CHANNELS, ScheduleClient, save_snapshot
from greek_tv.scraper.parser import parse_schedule


def ingest_schedule(
    *,
    channel: str,
    schedule_date: date,
    database_path: Path,
    raw_root: Path,
    client: ScheduleClient | None = None,
) -> tuple[int, Path]:
    normalized_channel = channel.lower()
    channel_id, channel_name = CHANNELS[normalized_channel]
    client = client or ScheduleClient()
    retrieved_at = datetime.now(UTC)
    html, source_url = client.fetch(normalized_channel, schedule_date)
    snapshot_path = save_snapshot(html, raw_root, normalized_channel, schedule_date)
    broadcasts = parse_schedule(
        html,
        channel_id=channel_id,
        channel=channel_name,
        schedule_date=schedule_date,
        source_url=source_url,
        retrieved_at=retrieved_at,
    )
    return BroadcastRepository(database_path).upsert(broadcasts), snapshot_path
