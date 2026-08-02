import argparse
import logging
from datetime import date

import httpx

from greek_tv.config import database_path, http_max_attempts, http_timeout_seconds, raw_data_dir
from greek_tv.ingestion.batch import BatchIngestionResult, ingest_all_schedules
from greek_tv.logger import configure_logging
from greek_tv.models import IngestionStatus
from greek_tv.scraper.channels import ChannelCatalogError
from greek_tv.scraper.client import ScheduleClient
from greek_tv.scraper.schedule import IngestionError, ingest_schedule


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="greek-tv")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest", help="fetch and store one channel schedule")
    ingest.add_argument("--channel", required=True)
    ingest.add_argument("--date", type=date.fromisoformat, required=True, metavar="YYYY-MM-DD")
    ingest_all = commands.add_parser("ingest-all", help="fetch and store every channel schedule")
    ingest_all.add_argument("--date", type=date.fromisoformat, required=True, metavar="YYYY-MM-DD")
    commands.add_parser("channels", help="list channels currently advertised by the source")
    return parser


def main() -> None:
    configure_logging()
    args = build_parser().parse_args()
    if args.command == "channels":
        client = ScheduleClient(
            timeout=http_timeout_seconds(),
            max_attempts=http_max_attempts(),
        )
        try:
            channels = client.fetch_catalog()
        except (ChannelCatalogError, httpx.HTTPError) as error:
            logging.getLogger(__name__).error("channel discovery failed: %s", error)
            raise SystemExit(1) from error
        for channel in channels:
            print(f"{channel.slug:<16} {channel.source_id:<4} {channel.display_name}")
        return
    if args.command == "ingest-all":
        try:
            result = ingest_all_schedules(
                schedule_date=args.date,
                database_path=database_path(),
                raw_root=raw_data_dir(),
            )
        except (ChannelCatalogError, httpx.HTTPError) as error:
            logging.getLogger(__name__).error("batch discovery failed: %s", error)
            raise SystemExit(1) from error
        _print_batch_summary(result)
        if not result.all_succeeded:
            raise SystemExit(1)
        return
    if args.command == "ingest":
        logger = logging.getLogger(__name__)
        try:
            run = ingest_schedule(
                channel=args.channel,
                schedule_date=args.date,
                database_path=database_path(),
                raw_root=raw_data_dir(),
            )
        except (ChannelCatalogError, ValueError, httpx.HTTPError) as error:
            logger.error("ingestion could not start: %s", error)
            raise SystemExit(1) from error
        except IngestionError as error:
            logger.error("run_id=%s status=failed error=%s", error.run_id, error.cause)
            raise SystemExit(1) from error
        logger.info(
            "run_id=%s status=%s channel=%s records=%d snapshot=%s",
            run.run_id,
            run.status,
            run.channel,
            run.records_parsed,
            run.snapshot_path,
        )


def _print_batch_summary(result: BatchIngestionResult) -> None:
    print(
        f"date={result.schedule_date.isoformat()} "
        f"succeeded={result.succeeded} failed={result.failed}"
    )
    print()
    for item in result.channels:
        detail = (
            f"{item.records_parsed} records"
            if item.status is IngestionStatus.SUCCEEDED
            else item.error_message
        )
        print(f"{item.channel.slug:<16} {item.status.value:<9} {detail}")


if __name__ == "__main__":
    main()
