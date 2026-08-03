import argparse
import logging
from datetime import date

import httpx

from greek_tv.config import (
    database_path,
    http_max_attempts,
    http_timeout_seconds,
    raw_data_dir,
    tmdb_access_token,
)
from greek_tv.enrichment import (
    TmdbCandidateRepository,
    TmdbClient,
    extract_title_evidence,
    normalize_title,
)
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
    tmdb_search = commands.add_parser(
        "tmdb-search", help="retrieve and cache TMDB candidates for one source title"
    )
    tmdb_search.add_argument("--title", required=True)
    tmdb_search.add_argument(
        "--query", help="override the TMDB query while retaining the source title"
    )
    tmdb_search.add_argument(
        "--description", help="source description containing additional title evidence"
    )
    tmdb_search.add_argument("--language", default="el-GR")
    tmdb_search.add_argument("--refresh", action="store_true")
    return parser


def main() -> None:
    configure_logging()
    args = build_parser().parse_args()
    if args.command == "tmdb-search":
        _search_tmdb(args.title, args.description, args.query, args.language, args.refresh)
        return
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


def _search_tmdb(
    source_title: str,
    description: str | None,
    query_override: str | None,
    language: str,
    refresh: bool,
) -> None:
    try:
        evidence = extract_title_evidence(source_title, description)
        queries = (
            (normalize_title(query_override).search_title,)
            if query_override
            else evidence.query_titles
        )
    except ValueError as error:
        logging.getLogger(__name__).error("TMDB search failed: %s", error)
        raise SystemExit(1) from error
    repository = TmdbCandidateRepository(database_path())
    result = None
    cache_status = "cached"
    for query in queries:
        cache_key = normalize_title(query).normalized_title
        result = None if refresh else repository.latest(cache_key, language)
        cache_status = "cached"
        if result is None:
            try:
                token = tmdb_access_token()
                response = TmdbClient(
                    token,
                    timeout=http_timeout_seconds(),
                    max_attempts=http_max_attempts(),
                ).search(query, language)
            except (ValueError, httpx.HTTPError) as error:
                logging.getLogger(__name__).error("TMDB search failed: %s", error)
                raise SystemExit(1) from error
            result = repository.save(cache_key, query, language, response)
            cache_status = "retrieved"
        if result.candidates:
            break

    if result is None:
        raise RuntimeError("title evidence produced no TMDB queries")

    lookup = repository.record_lookup(
        evidence,
        result.search_id,
        used_query_override=query_override is not None,
    )
    persisted_resolution = repository.resolve_lookup(lookup.lookup_id)
    resolution = persisted_resolution.resolution

    print(
        f"query={result.search_query!r} language={result.language} "
        f"status={cache_status} candidates={len(result.candidates)} "
        f"lookup_id={lookup.lookup_id}"
    )
    print(
        f"resolution={resolution.status.value} reason={resolution.reason.value} "
        f"score_margin={resolution.score_margin}"
    )
    for candidate in result.candidates:
        score = next(item for item in resolution.scores if item.candidate.rank == candidate.rank)
        year = candidate.release_date.year if candidate.release_date else "-"
        print(
            f"{candidate.rank:>2}  {candidate.media_type:<5} "
            f"tmdb_id={candidate.tmdb_id:<8} year={year} "
            f"score={score.total_score:>6.2f} rank={score.score_rank:<2} {candidate.title}"
        )


if __name__ == "__main__":
    main()
