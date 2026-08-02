import argparse
import logging
from datetime import date

from greek_tv.config import database_path, raw_data_dir
from greek_tv.logger import configure_logging
from greek_tv.scraper.client import CHANNELS
from greek_tv.scraper.schedule import IngestionError, ingest_schedule


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="greek-tv")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest", help="fetch and store one channel schedule")
    ingest.add_argument("--channel", choices=sorted(CHANNELS), required=True)
    ingest.add_argument("--date", type=date.fromisoformat, required=True, metavar="YYYY-MM-DD")
    return parser


def main() -> None:
    configure_logging()
    args = build_parser().parse_args()
    if args.command == "ingest":
        logger = logging.getLogger(__name__)
        try:
            run = ingest_schedule(
                channel=args.channel,
                schedule_date=args.date,
                database_path=database_path(),
                raw_root=raw_data_dir(),
            )
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


if __name__ == "__main__":
    main()
