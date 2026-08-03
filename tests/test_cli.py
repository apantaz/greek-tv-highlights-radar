from datetime import date

import pytest

from greek_tv import cli
from greek_tv.ingestion.batch import BatchIngestionResult, ChannelIngestionResult
from greek_tv.models import IngestionStatus
from greek_tv.scraper.channels import Channel


class CatalogClient:
    def __init__(self, **_kwargs) -> None:
        pass

    def fetch_catalog(self) -> tuple[Channel, ...]:
        return (
            Channel("ert1", 18, "ΕΡΤ1"),
            Channel("channel-200", 200, "ΝΕΟ"),
        )


def test_channels_command_lists_live_catalog(monkeypatch, capsys):
    monkeypatch.setattr(cli, "ScheduleClient", CatalogClient)
    monkeypatch.setattr("sys.argv", ["greek-tv", "channels"])

    cli.main()

    assert [line.split() for line in capsys.readouterr().out.splitlines()] == [
        ["ert1", "18", "ΕΡΤ1"],
        ["channel-200", "200", "ΝΕΟ"],
    ]


def test_ingest_parser_accepts_dynamic_channel_slug():
    args = cli.build_parser().parse_args(
        ["ingest", "--channel", "channel-200", "--date", "2026-08-02"]
    )

    assert args.channel == "channel-200"


def test_tmdb_search_parser_exposes_language_and_refresh_controls():
    args = cli.build_parser().parse_args(
        [
            "tmdb-search",
            "--title",
            "Το Σόι σου",
            "--query",
            "To Soi Sou",
            "--language",
            "en-US",
            "--refresh",
        ]
    )

    assert args.title == "Το Σόι σου"
    assert args.query == "To Soi Sou"
    assert args.language == "en-US"
    assert args.refresh is True


def test_tmdb_check_reports_valid_connection(monkeypatch, capsys):
    class ValidClient:
        def validate_access_token(self) -> None:
            pass

    monkeypatch.setattr(cli, "_tmdb_client", ValidClient)
    monkeypatch.setattr("sys.argv", ["greek-tv", "tmdb-check"])

    cli.main()

    assert capsys.readouterr().out.strip() == "TMDB connection OK: read-access token is valid"


def test_enrich_parser_exposes_language_and_incremental_limit():
    args = cli.build_parser().parse_args(
        [
            "enrich",
            "--language",
            "en-US",
            "--limit",
            "10",
            "--channel",
            "star",
            "--date",
            "2026-08-01",
        ]
    )

    assert args.language == "en-US"
    assert args.limit == 10
    assert args.channel == "star"
    assert args.date == date(2026, 8, 1)


def test_enrich_entities_parser_exposes_cache_controls():
    args = cli.build_parser().parse_args(
        ["enrich-entities", "--language", "en-US", "--limit", "5", "--refresh"]
    )

    assert args.language == "en-US"
    assert args.limit == 5
    assert args.refresh is True


def batch_result(*, failed: bool) -> BatchIngestionResult:
    results = [
        ChannelIngestionResult(
            channel=Channel("ert1", 18, "ΕΡΤ1"),
            status=IngestionStatus.SUCCEEDED,
            run_id="run-1",
            records_parsed=20,
        )
    ]
    if failed:
        results.append(
            ChannelIngestionResult(
                channel=Channel("ert2", 87, "ΕΡΤ2"),
                status=IngestionStatus.FAILED,
                run_id="run-2",
                records_parsed=0,
                error_message="RuntimeError: unavailable",
            )
        )
    return BatchIngestionResult(date(2026, 8, 2), tuple(results))


def test_ingest_all_prints_summary_and_succeeds(monkeypatch, capsys):
    monkeypatch.setattr(cli, "ingest_all_schedules", lambda **_kwargs: batch_result(failed=False))
    monkeypatch.setattr("sys.argv", ["greek-tv", "ingest-all", "--date", "2026-08-02"])

    cli.main()

    output = capsys.readouterr().out
    assert "date=2026-08-02 succeeded=1 failed=0" in output
    assert "ert1" in output
    assert "succeeded 20 records" in output


def test_ingest_all_exits_nonzero_after_partial_failure(monkeypatch, capsys):
    monkeypatch.setattr(cli, "ingest_all_schedules", lambda **_kwargs: batch_result(failed=True))
    monkeypatch.setattr("sys.argv", ["greek-tv", "ingest-all", "--date", "2026-08-02"])

    with pytest.raises(SystemExit) as captured:
        cli.main()

    assert captured.value.code == 1
    output = capsys.readouterr().out
    assert "date=2026-08-02 succeeded=1 failed=1" in output
    assert "ert2" in output
    assert "failed    RuntimeError: unavailable" in output
