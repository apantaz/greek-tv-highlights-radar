import pytest

from greek_tv.enrichment import normalize_title


@pytest.mark.parametrize(
    ("source_title", "expected_title"),
    [
        ("Ειδήσεις – Αθλητικά – Καιρός", "ειδησεισ αθλητικα καιροσ"),
        ("Η Μαρία που Έγινε Κάλλας", "η μαρια που εγινε καλλασ"),
        ("L.O.L. Surprise! Family / Beep Boop", "l o l surprise family beep boop"),
        ("  Το   Σόι σου, ΙΙ  ", "το σοι σου ιι"),
    ],
)
def test_normalizes_case_accents_punctuation_and_whitespace(source_title, expected_title):
    result = normalize_title(source_title)

    assert result.normalized_title == expected_title


@pytest.mark.parametrize("rating", ["K8", "Κ8"])
def test_extracts_content_rating_prefix(rating):
    result = normalize_title(f"[{rating}] Ξένη Ταινία")

    assert result.original_title == f"[{rating}] Ξένη Ταινία"
    assert result.search_title == "Ξένη Ταινία"
    assert result.normalized_title == "ξενη ταινια"
    assert result.content_rating == "K8"
    assert result.is_repeat is False


@pytest.mark.parametrize("marker", ["Ε", "E", "ε", "e"])
def test_extracts_trailing_repeat_marker(marker):
    result = normalize_title(f"Happy Traveller ({marker})")

    assert result.normalized_title == "happy traveller"
    assert result.search_title == "Happy Traveller"
    assert result.is_repeat is True


def test_preserves_parenthesized_alternate_title():
    result = normalize_title("[K8] Η Μάνα του 10αριού (La Mama del 10)")

    assert result.normalized_title == "η μανα του 10αριου la mama del 10"
    assert result.content_rating == "K8"
    assert result.is_repeat is False


@pytest.mark.parametrize("title", ["", "   ", "[K8] (Ε)"])
def test_rejects_titles_without_searchable_characters(title):
    with pytest.raises(ValueError, match="title"):
        normalize_title(title)
