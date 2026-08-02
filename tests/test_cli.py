from greek_tv import cli
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
