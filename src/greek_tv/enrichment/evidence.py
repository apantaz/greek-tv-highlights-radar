"""Extract explicit entity-resolution evidence from schedule text."""

import re
from dataclasses import dataclass

from greek_tv.enrichment.titles import normalize_title

_PARENTHESIZED_TEXT = re.compile(r"\(([^()]*)\)")
_LEADING_BRACKETED_TEXT = re.compile(r"^\s*\[([^]]+)]")
_LATIN_LETTER = re.compile(r"[A-Za-z]")
_PRODUCTION_YEAR = re.compile(
    r"(?:έτος\s+παραγωγής\s*:\s*|παραγωγής?\s+)(19\d{2}|20\d{2})",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class TitleEvidence:
    """Explicit search variants and production year found in source text."""

    source_title: str
    query_titles: tuple[str, ...]
    production_year: int | None


def extract_title_evidence(title: str, description: str | None = None) -> TitleEvidence:
    """Extract only source-provided title variants and a stated production year."""
    normalized = normalize_title(title)
    query_titles: list[str] = []

    for match in _PARENTHESIZED_TEXT.finditer(normalized.search_title):
        _append_latin_variant(query_titles, match.group(1))

    if description:
        bracketed = _LEADING_BRACKETED_TEXT.match(description)
        if bracketed:
            _append_latin_variant(query_titles, bracketed.group(1))

    title_without_variants = _PARENTHESIZED_TEXT.sub(" ", normalized.search_title)
    source_query = " ".join(title_without_variants.split())
    if source_query:
        _append_unique(query_titles, source_query)
    if not query_titles:
        query_titles.append(normalized.search_title)

    year_match = _PRODUCTION_YEAR.search(description or "")
    production_year = int(year_match.group(1)) if year_match else None
    return TitleEvidence(normalized.original_title, tuple(query_titles), production_year)


def _append_latin_variant(variants: list[str], value: str) -> None:
    value = " ".join(value.split())
    if value and _LATIN_LETTER.search(value):
        _append_unique(variants, value)


def _append_unique(variants: list[str], value: str) -> None:
    identity = normalize_title(value).normalized_title
    if all(normalize_title(existing).normalized_title != identity for existing in variants):
        variants.append(value)
