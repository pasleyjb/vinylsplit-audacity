"""Tests for the Track List wizard page."""

from __future__ import annotations

import pytest

from vinylsplit.metadata.models import (
    Artist,
    Medium,
    Release,
    Track,
)
from vinylsplit.metadata.session import WizardSession
from vinylsplit.wizard.pages.track_list_page import TrackListPage


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
def track_page(container, session) -> TrackListPage:
    page = TrackListPage(container)
    page.show()
    return page


def test_initialize_populates_track_table(
    track_page: TrackListPage, session: WizardSession
) -> None:
    session.set_selected_release(_sample_release())
    track_page.initializePage()

    assert track_page.track_table.rowCount() == 2
    assert track_page.track_table.item(0, 1).text() == "Speak to Me"
    assert track_page.track_table.item(0, 2).text() == "1:30"
    assert track_page.track_table.item(1, 2).text() == "2:43"
    assert track_page.isComplete() is True