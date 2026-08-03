"""Deterministic programme-title normalization for metadata candidate searches.

The source title remains the authoritative observation. Normalization produces a
separate search value and extracts only explicit source annotations; it does not try
to infer programme type, season, or alternate-title semantics.
"""

import re
import unicodedata
from dataclasses import dataclass

_CONTENT_RATING_PREFIX = re.compile(r"^\[\s*([KΚ](?:\d{1,2})?)\s*\]\s*", re.IGNORECASE)
_REPEAT_SUFFIX = re.compile(r"\s*\(([ΕE])\)\s*$", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class NormalizedTitle:
    """A source title and the explicit metadata extracted from it."""

    original_title: str
    search_title: str
    normalized_title: str
    content_rating: str | None
    is_repeat: bool


def normalize_title(title: str) -> NormalizedTitle:
    """Normalize a source title without discarding its authoritative representation.

    The search form is case-insensitive, accent-insensitive, punctuation-neutral, and
    whitespace-normalized. Leading Greek TV content ratings such as ``[K8]`` and
    trailing Greek or Latin repeat markers are extracted because they are schedule
    annotations rather than programme identity.

    Args:
        title: Programme title exactly as supplied by the schedule source.

    Returns:
        The preserved source title, normalized search title, and extracted metadata.

    Raises:
        ValueError: If the input is blank or contains no searchable characters after
            removing explicit schedule annotations.
    """
    original_title = " ".join(title.split())
    if not original_title:
        raise ValueError("title must contain non-whitespace characters")

    candidate = original_title
    rating_match = _CONTENT_RATING_PREFIX.match(candidate)
    content_rating = None
    if rating_match:
        content_rating = rating_match.group(1).upper().replace("Κ", "K")
        candidate = candidate[rating_match.end() :]

    repeat_match = _REPEAT_SUFFIX.search(candidate)
    is_repeat = repeat_match is not None
    if repeat_match:
        candidate = candidate[: repeat_match.start()]

    search_title = candidate.strip()

    decomposed = unicodedata.normalize("NFKD", candidate.casefold())
    without_accents = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    normalized_title = " ".join(
        "".join(character if character.isalnum() else " " for character in without_accents).split()
    )
    if not normalized_title:
        raise ValueError("title contains no searchable characters after normalization")

    return NormalizedTitle(
        original_title=original_title,
        search_title=search_title,
        normalized_title=normalized_title,
        content_rating=content_rating,
        is_repeat=is_repeat,
    )
