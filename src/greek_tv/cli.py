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
)
from greek_tv.enrichment.batch import (
    BatchEnrichmentResult,
    BatchEnrichmentStatus,
    enrich_current_programmes,
)
from greek_tv.enrichment.entity_batch import (
    BatchEntityEnrichmentResult,
    EntityEnrichmentStatus,
    enrich_matched_entities,
)
from greek_tv.enrichment.service import enrich_title
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
    enrich = commands.add_parser("enrich", help="enrich all distinct current programmes")
    enrich.add_argument("--language", default="el-GR")
    enrich.add_argument("--limit", type=_positive_int)
    enrich.add_argument("--channel")
    enrich.add_argument("--date", type=date.fromisoformat, metavar="YYYY-MM-DD")
    enrich_entities = commands.add_parser(
        "enrich-entities",
        help="retrieve full metadata for confidently matched TMDB identities",
    )
    enrich_entities.add_argument("--language", default="el-GR")
    enrich_entities.add_argument("--limit", type=_positive_int)
    enrich_entities.add_argument("--refresh", action="store_true")
    return parser


def main() -> None:
    configure_logging()
    args = build_parser().parse_args()
    if args.command == "tmdb-search":
        _search_tmdb(args.title, args.description, args.query, args.language, args.refresh)
        return
    if args.command == "enrich":
        result = enrich_current_programmes(
            database_path(),
            language=args.language,
            client_factory=_tmdb_client,
            limit=args.limit,
            channel=args.channel,
            schedule_date=args.date,
        )
        _print_enrichment_summary(result)
        if result.failed:
            raise SystemExit(1)
        return
    if args.command == "enrich-entities":
        result = enrich_matched_entities(
            database_path(),
            language=args.language,
            client_factory=_tmdb_client,
            limit=args.limit,
            refresh=args.refresh,
        )
        _print_entity_enrichment_summary(result)
        if result.failed:
            raise SystemExit(1)
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


def _print_entity_enrichment_summary(result: BatchEntityEnrichmentResult) -> None:
    print(
        f"total={result.total} "
        f"retrieved={result.count(EntityEnrichmentStatus.RETRIEVED)} "
        f"cached={result.count(EntityEnrichmentStatus.CACHED)} "
        f"failed={result.failed}"
    )
    print()
    for item in result.entities:
        detail = item.error_message or ""
        print(f"{item.media_type:<5} {item.tmdb_id:<8} {item.status.value:<9} {detail}")


def _search_tmdb(
    source_title: str,
    description: str | None,
    query_override: str | None,
    language: str,
    refresh: bool,
) -> None:
    try:
        outcome = enrich_title(
            TmdbCandidateRepository(database_path()),
            source_title,
            description,
            language=language,
            client_factory=_tmdb_client,
            query_override=query_override,
            refresh=refresh,
        )
    except (ValueError, httpx.HTTPError) as error:
        logging.getLogger(__name__).error("TMDB search failed: %s", error)
        raise SystemExit(1) from error
    result = outcome.search
    resolution = outcome.resolution.resolution

    print(
        f"query={result.search_query!r} language={result.language} "
        f"status={outcome.search_source.value} candidates={len(result.candidates)} "
        f"lookup_id={outcome.lookup.lookup_id}"
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


def _tmdb_client() -> TmdbClient:
    return TmdbClient(
        tmdb_access_token(),
        timeout=http_timeout_seconds(),
        max_attempts=http_max_attempts(),
    )


def _print_enrichment_summary(result: BatchEnrichmentResult) -> None:
    print(
        f"total={result.total} "
        f"matched={result.count(BatchEnrichmentStatus.MATCHED)} "
        f"unresolved={result.count(BatchEnrichmentStatus.UNRESOLVED)} "
        f"skipped={result.count(BatchEnrichmentStatus.SKIPPED)} "
        f"failed={result.failed} cached={result.cached} retrieved={result.retrieved}"
    )
    print()
    for item in result.programmes:
        detail = item.error_message or (item.search_source.value if item.search_source else "")
        print(f"{item.status.value:<10} {item.source_title} {detail}".rstrip())


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise ValueError("value must be at least 1")
    return parsed


if __name__ == "__main__":
    main()
