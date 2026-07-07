"""Tests for the Artist & Album Search wizard page."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt

from vinylsplit.metadata.models import (
    Artist,
    Medium,
    Release,
    ReleaseSummary,
    Track,
)
from vinylsplit.metadata.session import WizardSession
from vinylsplit.musicbrainz.client import MusicBrainzClient
from vinylsplit.wizard.pages.artist_search_page import (
    AlbumSearchResult,
    ArtistSearchPage,
    ReleaseFetchResult,
)


@pytest.fixture
def musicbrainz_client() -> MagicMock:
    return MagicMock(spec=MusicBrainzClient)


@pytest.fixture
def search_page(container, session, musicbrainz_client) -> ArtistSearchPage:
    page = ArtistSearchPage(container, musicbrainz_client=musicbrainz_client)
    page.show()
    return page


def _sample_summary() -> ReleaseSummary:
    return ReleaseSummary(
        id="release-mbid-1",
        artist="Pink Floyd",
        album="The Dark Side of the Moon",
        release_year="1973",
        country="GB",
        track_count=10,
        release_type="Album",
    )


def _sample_release() -> Release:
    return Release(
        id="release-mbid-1",
        title="The Dark Side of the Moon",
        artist=Artist(id="artist-mbid-1", name="Pink Floyd"),
        date="1973-03-01",
        country="GB",
        release_year="1973",
        release_type="Album",
        track_count=1,
        status="Official",
        media=(
            Medium(
                position=1,
                format="Vinyl",
                track_count=1,
                tracks=(
                    Track(
                        id="track-mbid-1",
                        title="Speak to Me",
                        position=1,
                        number="1",
                        length_ms=90000,
                    ),
                ),
            ),
        ),
    )


def test_search_page_requires_input_before_search(
    search_page: ArtistSearchPage,
) -> None:
    search_page.artist_input.clear()
    search_page.album_input.clear()
    search_page._on_search_clicked()

    assert "Enter an artist or album" in search_page._status_label.text()


def test_apply_search_result_populates_table(
    search_page: ArtistSearchPage,
    session: WizardSession,
) -> None:
    search_page.apply_search_result(
        AlbumSearchResult(summaries=(_sample_summary(), _sample_summary()))
    )

    assert search_page._results_table.rowCount() == 2
    assert search_page._results_table.item(0, 0).text() == "Pink Floyd"
    assert len(session.search_results) == 2


def test_apply_search_result_no_results(search_page: ArtistSearchPage) -> None:
    search_page.apply_search_result(AlbumSearchResult())

    assert search_page._results_table.rowCount() == 0
    assert "No releases found" in search_page._status_label.text()


def test_apply_search_result_shows_error(search_page: ArtistSearchPage) -> None:
    search_page.apply_search_result(
        AlbumSearchResult(
            error="Unable to reach MusicBrainz. Check your internet connection."
        )
    )

    assert search_page._results_table.rowCount() == 0
    assert "internet connection" in search_page._status_label.text()


def test_release_selection_stores_session_state(
    search_page: ArtistSearchPage,
    session: WizardSession,
) -> None:
    search_page.apply_search_result(AlbumSearchResult(summaries=(_sample_summary(),)))
    search_page.apply_release_fetch_result(
        ReleaseFetchResult(release=_sample_release())
    )

    assert session.selected_release is not None
    assert session.selected_release.id == "release-mbid-1"
    assert search_page.isComplete() is True
    assert "Selected:" in search_page._status_label.text()


def test_search_button_runs_in_background(
    qtbot,
    container,
    session,
    musicbrainz_client: MagicMock,
) -> None:
    musicbrainz_client.search_releases.return_value = [_sample_summary()]

    page = ArtistSearchPage(container, musicbrainz_client=musicbrainz_client)
    qtbot.addWidget(page)
    page.artist_input.setText("Pink Floyd")
    page.album_input.setText("The Dark Side of the Moon")

    qtbot.mouseClick(page._search_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: page._results_table.rowCount() == 1, timeout=2000)

    musicbrainz_client.search_releases.assert_called_once_with(
        "Pink Floyd",
        "The Dark Side of the Moon",
    )
    assert page._search_button.isEnabled() is True
    assert page._progress_bar.isVisible() is False


def test_container_injects_session_and_registers_musicbrainz(container) -> None:
    assert isinstance(container.session, WizardSession)
    assert isinstance(container.resolve("musicbrainz"), MusicBrainzClient)
