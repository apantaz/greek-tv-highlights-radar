import pytest

from greek_tv.scraper.channels import (
    ChannelCatalogError,
    parse_channel_catalog,
    resolve_channel,
)


def test_discovers_current_source_catalog(channel_catalog_html):
    channels = parse_channel_catalog(channel_catalog_html)

    assert len(channels) == 18
    assert channels[0].slug == "ert1"
    assert channels[0].source_id == 18
    assert channels[0].display_name == "ΕΡΤ1"
    assert channels[0].logo_url == "https://programmatileorasis.gr/images/logo_ert1.jpg"
    assert channels[-1].slug == "ert-news"


def test_assigns_stable_fallback_to_new_channel():
    html = '<div class="channels_list"><a href="/free/200/ΝΕΟ"><img alt="ΝΕΟ"></a></div>'

    assert parse_channel_catalog(html)[0].slug == "channel-200"


@pytest.mark.parametrize("selector", ["ert1", "18", "ΕΡΤ1"])
def test_resolves_slug_identifier_or_display_name(channel_catalog_html, selector):
    channel = resolve_channel(parse_channel_catalog(channel_catalog_html), selector)

    assert channel.source_id == 18


@pytest.mark.parametrize(
    ("html", "message"),
    [
        ("<html></html>", "channels_list was not found"),
        ('<div class="channels_list"></div>', "contains no free channels"),
        (
            '<div class="channels_list"><a href="/free/not-an-id/name"></a></div>',
            "malformed channel link",
        ),
    ],
)
def test_rejects_malformed_catalog(html, message):
    with pytest.raises(ChannelCatalogError, match=message):
        parse_channel_catalog(html)


def test_rejects_channel_not_in_live_catalog(channel_catalog_html):
    channels = parse_channel_catalog(channel_catalog_html)

    with pytest.raises(ValueError, match="not currently available"):
        resolve_channel(channels, "removed-channel")
