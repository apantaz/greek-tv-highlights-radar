from pathlib import Path

import pytest


@pytest.fixture
def schedule_html() -> str:
    fixture = (
        Path(__file__).parent
        / "fixtures"
        / "schedules"
        / ("programmatileorasis_ert1_2026-07-19.html")
    )
    return fixture.read_text(encoding="utf-8")
