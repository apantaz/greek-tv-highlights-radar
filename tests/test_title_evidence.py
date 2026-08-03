import pytest

from greek_tv.enrichment import extract_title_evidence


@pytest.mark.parametrize(
    ("title", "expected_queries"),
    [
        ("Ο Φυγάς (The Fugitive)", ("The Fugitive", "Ο Φυγάς")),
        (
            "[K8] Η Μάνα του 10αριού (La Mama del 10)",
            ("La Mama del 10", "Η Μάνα του 10αριού"),
        ),
        ("Inception", ("Inception",)),
    ],
)
def test_extracts_source_provided_title_variants(title, expected_queries):
    evidence = extract_title_evidence(title)

    assert evidence.source_title == title
    assert evidence.query_titles == expected_queries


def test_extracts_bracketed_title_and_production_year_from_description():
    evidence = extract_title_evidence(
        "Χριστουγεννιάτικος Έρωτας στο Καταφύγιο",
        "[Let it Snow] Έτος παραγωγής: 2013 Η Στέφανι φτάνει στο καταφύγιο.",
    )

    assert evidence.query_titles == (
        "Let it Snow",
        "Χριστουγεννιάτικος Έρωτας στο Καταφύγιο",
    )
    assert evidence.production_year == 2013


def test_does_not_treat_greek_metadata_brackets_as_international_title():
    evidence = extract_title_evidence(
        "Ο Φυγάς",
        "[Κ12 - Περιέχει σκηνές βίας]. Αμερικανική παραγωγή 1993.",
    )

    assert evidence.query_titles == ("Ο Φυγάς",)
    assert evidence.production_year == 1993
