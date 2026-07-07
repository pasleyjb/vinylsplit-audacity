"""Tests for the Review Album Layout wizard page."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from vinylsplit.audacity.client import AudacityClient
from vinylsplit.metadata.models import (
    Artist,
    Medium,
    Release,
    Track,
)
from vinylsplit.metadata.session import WizardSession
from vinylsplit.wizard.pages.review_page import ReviewPage


@pytest.fixture
def audacity_client() -> MagicMock:
    return MagicMock(spec=AudacityClient)


def _sample_release() -> Release:
    return Release(
        id="release-mbid-1",
        title="The Dark Side of the Moon",
        artist=Artist(id="artist-mbid-1", name="Pink Floyd"),
        date="1973-03-01",
        country="GB",
        release_year="1973",
        release_type="Album",
        track_count=2,
        status="Official",
        media=(
            Medium(
                position=1,
                format="Vinyl",
                track_count=2,
                tracks=(
                    Track(
                        id="track-1",
                        title="Speak to Me",
                        position=1,
                        number="1",
                        length_ms=90_000,
                    ),
                    Track(
                        id="track-2",
                        title="Breathe",
                        position=2,
                        number="2",
                        length_ms=163_000,
                    ),
                ),
            ),
        ),
    )


@pytest.fixture
def review_page(container, session, audacity_client) -> ReviewPage:
    page = ReviewPage(container, audacity_client=audacity_client)
    page.show()
    return page


def test_refresh_populates_review_table(
    review_page: ReviewPage, session: WizardSession
) -> None:
    session.set_selected_release(_sample_release())
    session.mark_initial_regions_generated(2)

    review_page.apply_refresh_regions(
        [
            {"text": "01 Speak to Me", "start": 0.0, "end": 90.0},
            {"text": "02 Breathe", "start": 90.0, "end": 253.0},
        ]
    )

    assert review_page._review_table.rowCount() == 2
    assert review_page._review_table.item(0, 2).text() == "00:00 → 01:30"
    assert review_page._review_table.item(1, 5).text() == "✓"
    assert session.layout_review_refreshed is True
    assert review_page.isComplete() is True


def test_refresh_shows_warning_for_large_difference(
    review_page: ReviewPage, session: WizardSession
) -> None:
    session.set_selected_release(_sample_release())
    session.mark_initial_regions_generated(2)

    review_page.apply_refresh_regions(
        [
            {"text": "01 Speak to Me", "start": 0.0, "end": 90.0},
            {"text": "02 Breathe", "start": 95.0, "end": 258.0},
        ]
    )

    assert review_page._review_table.item(1, 5).text() == "⚠ Warning"
    assert "more than 2 seconds" in review_page._status_label.text()