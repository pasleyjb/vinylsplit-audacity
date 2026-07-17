"""Tests for the Generate Album Layout wizard page."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from vinylsplit.audacity.client import AudacityClient
from vinylsplit.labels.audacity_regions import RegionGenerationResult
from vinylsplit.metadata.models import (
    Artist,
    Medium,
    Release,
    Track,
)
from vinylsplit.metadata.session import WizardSession
from vinylsplit.wizard.pages.generate_album_layout_page import GenerateAlbumLayoutPage


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
def layout_page(container, session, audacity_client) -> GenerateAlbumLayoutPage:
    page = GenerateAlbumLayoutPage(container, audacity_client=audacity_client)
    page.show()
    return page


def test_initialize_populates_preview_table(
    layout_page: GenerateAlbumLayoutPage, session: WizardSession
) -> None:
    session.set_selected_release(_sample_release())
    layout_page.initializePage()

    assert layout_page._preview_table.rowCount() == 2
    assert layout_page._preview_table.item(0, 1).text() == "Speak to Me"
    assert layout_page._preview_table.item(0, 2).text() == "00:00 → 01:30"
    assert layout_page._preview_table.item(1, 2).text() == "01:30 → 04:13"


def test_generate_regions_updates_session(
    layout_page: GenerateAlbumLayoutPage, session: WizardSession
) -> None:
    session.set_selected_release(_sample_release())
    layout_page.initializePage()
    layout_page.apply_region_generation_result(
        RegionGenerationResult(success=True, message="ok", regions_created=2)
    )

    assert session.initial_regions_generated is True
    assert session.regions_created_count == 2
    assert session.layout_review_refreshed is True
    assert session.skipped_region_generation is False
    assert layout_page.isComplete() is True
    assert session.ready_for_export() is True


def test_layout_edit_updates_preview(
    layout_page: GenerateAlbumLayoutPage, session: WizardSession
) -> None:
    from vinylsplit.labels.layout_engine import AlbumLayout, TrackRegion

    session.set_selected_release(_sample_release())
    layout_page.initializePage()
    assert layout_page._preview_table.item(0, 2).text() == "00:00 → 01:30"

    edited = AlbumLayout(
        release_id="release-mbid-1",
        artist_name="Pink Floyd",
        album_title="The Dark Side of the Moon",
        regions=(
            TrackRegion(0, "01", "Speak to Me", "01 Speak to Me", 30.0, 120.0),
            TrackRegion(1, "02", "Breathe", "02 Breathe", 120.0, 283.0),
        ),
    )
    layout_page._on_layout_changed(edited)

    assert session.layout_offset_seconds == 30.0
    assert layout_page._preview_table.item(0, 2).text() == "00:30 → 02:00"
    assert layout_page.isComplete() is False


def test_skip_uses_existing_labels(
    layout_page: GenerateAlbumLayoutPage, session: WizardSession
) -> None:
    session.set_selected_release(_sample_release())
    layout_page.initializePage()

    fake_labels = [
        {"title": "01 Speak to Me", "start": 0.0, "end": 90.0},
        {"title": "02 Breathe", "start": 90.0, "end": 253.0},
    ]
    layout_page.apply_skip_regions(fake_labels)

    assert session.skipped_region_generation is True
    assert session.initial_regions_generated is True
    assert session.layout_review_refreshed is True
    assert session.regions_created_count == 2
    assert layout_page.isComplete() is True
    assert "existing" in layout_page._status_label.text().lower()


def test_skip_with_no_labels_does_not_complete(
    layout_page: GenerateAlbumLayoutPage, session: WizardSession
) -> None:
    session.set_selected_release(_sample_release())
    layout_page.initializePage()
    layout_page.apply_skip_regions([])

    assert session.initial_regions_generated is False
    assert layout_page.isComplete() is False