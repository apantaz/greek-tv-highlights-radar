import argparse
import logging
from datetime import date

from greek_tv.config import database_path, raw_data_dir
from greek_tv.logger import configure_logging
from greek_tv.scraper.client import CHANNELS
from greek_tv.scraper.schedule import ingest_schedule


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
        count, snapshot = ingest_schedule(
            channel=args.channel,
            schedule_date=args.date,
            database_path=database_path(),
            raw_root=raw_data_dir(),
        )
        logging.getLogger(__name__).info("stored %d broadcasts; raw snapshot: %s", count, snapshot)


if __name__ == "__main__":
    main()
