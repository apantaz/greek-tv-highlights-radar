"""Discover and resolve channels advertised by ProgrammaTileorasis."""

import re
from dataclasses import dataclass
from urllib.parse import unquote

from bs4 import BeautifulSoup

CHANNEL_PATH = re.compile(r"^/free/(?P<source_id>\d+)/(?P<name>[^/?#]+)")

# Aliases are interface conveniences, not a source-of-truth catalog. Newly discovered
# source identifiers remain usable through their numeric ID or a channel-<id> slug.
KNOWN_ALIASES = {
    1: "mega",
    2: "ant1",
    3: "star",
    5: "alpha",
    6: "ert3",
    7: "skai",
    17: "mak-tv",
    18: "ert1",
    19: "mad",
    80: "vouli",
    87: "ert2",
    99: "open",
    121: "one",
    122: "smile",
    126: "action24",
    129: "ert-news",
    136: "keedoo",
    137: "naftemporiki",
}


class ChannelCatalogError(ValueError):
    """Raised when the upstream channel catalog cannot be interpreted safely."""


@dataclass(frozen=True, slots=True)
class Channel:
    """Identify one channel discovered in the upstream source catalog."""

    slug: str
    source_id: int
    display_name: str


def parse_channel_catalog(html: str) -> tuple[Channel, ...]:
    """Parse the current free-channel catalog from a source page."""
    soup = BeautifulSoup(html, "html.parser")
    catalog = soup.select_one(".channels_list")
    if catalog is None:
        raise ChannelCatalogError("channel catalog .channels_list was not found")

    channels: list[Channel] = []
    source_ids: set[int] = set()
    slugs: set[str] = set()
    for link in catalog.select('a[href^="/free/"]'):
        href = link.get("href", "")
        match = CHANNEL_PATH.match(href)
        if match is None:
            raise ChannelCatalogError(f"malformed channel link {href!r}")

        source_id = int(match.group("source_id"))
        image = link.select_one("img[alt]")
        display_name = image.get("alt", "").strip() if image else ""
        display_name = display_name or unquote(match.group("name")).strip()
        if not display_name:
            raise ChannelCatalogError(f"channel {source_id} has no display name")

        slug = KNOWN_ALIASES.get(source_id, f"channel-{source_id}")
        if source_id in source_ids or slug in slugs:
            raise ChannelCatalogError(f"duplicate channel entry for {slug!r}")
        source_ids.add(source_id)
        slugs.add(slug)
        channels.append(Channel(slug, source_id, display_name))

    if not channels:
        raise ChannelCatalogError("channel catalog contains no free channels")
    return tuple(channels)


def resolve_channel(channels: tuple[Channel, ...], selector: str) -> Channel:
    """Resolve a slug, source identifier, or display name against a live catalog."""
    normalized = selector.casefold()
    for channel in channels:
        if normalized in {
            channel.slug.casefold(),
            str(channel.source_id),
            channel.display_name.casefold(),
        }:
            return channel
    available = ", ".join(channel.slug for channel in channels)
    raise ValueError(f"channel {selector!r} is not currently available; choose one of: {available}")
