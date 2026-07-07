"""Tests for the Release Selection wizard page."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from vinylsplit.metadata.models import (
    Artist,
    Medium,
    Release,
    ReleaseSummary,
    Track,
)
from vinylsplit.metadata.session import WizardSession
from vinylsplit.musicbrainz.client import MusicBrainzClient
from vinylsplit.wizard.pages.release_selection_page import (
    ReleaseFetchResult,
    ReleaseSelectionPage,
)


@pytest.fixture
def musicbrainz_client() -> MagicMock:
    return MagicMock(spec=MusicBrainzClient)


@pytest.fixture
def release_page(container, session, musicbrainz_client) -> ReleaseSelectionPage:
    page = ReleaseSelectionPage(container, musicbrainz_client=musicbrainz_client)
    page.show()
    return page


def _sample_summary(release_id: str = "release-mbid-1") -> ReleaseSummary:
    return ReleaseSummary(
        id=release_id,
        artist="Pink Floyd",
        album="The Dark Side of the Moon",
        release_year="1973",
        country="GB",
        track_count=2,
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
        track_count=2,
        status="Official",
        media=(
            Medium(
                position=1,
                format="Vinyl",
                track_count=2,
                tracks=(
                    Track(
                        id="track-mbid-1",
                        title="Speak to Me",
                        position=1,
                        number="1",
                        length_ms=90000,
                    ),
                    Track(
                        id="track-mbid-2",
                        title="Breathe",
                        position=2,
                        number="2",
                        length_ms=163000,
                    ),
                ),
            ),
        ),
    )


def test_initialize_populates_release_list(
    release_page: ReleaseSelectionPage,
    session: WizardSession,
) -> None:
    session.search_results = [_sample_summary(), _sample_summary("release-mbid-2")]
    release_page.initializePage()

    assert release_page.release_list.count() == 2


def test_display_release_shows_numbered_tracks_and_table(
    release_page: ReleaseSelectionPage,
) -> None:
    release_page._display_release(_sample_release())

    assert "01 Speak to Me" in release_page._track_list_label.text()
    assert "02 Breathe" in release_page._track_list_label.text()
    assert release_page._track_table.rowCount() == 2
    assert release_page._track_table.item(0, 0).text() == "01"
    assert release_page._track_table.item(0, 1).text() == "Speak to Me"
    assert release_page._track_table.item(0, 2).text() == "1:30"


def test_apply_release_fetch_result_stores_session_state(
    release_page: ReleaseSelectionPage,
    session: WizardSession,
) -> None:
    session.search_results = [_sample_summary()]
    release_page.initializePage()
    release_page.apply_release_fetch_result(
        ReleaseFetchResult(release=_sample_release())
    )

    assert session.selected_release is not None
    assert session.selected_release.id == "release-mbid-1"
    assert len(session.track_list) == 2
    assert release_page.isComplete() is True
    assert "Loaded 2 official track(s)" in release_page._status_label.text()


def test_apply_release_fetch_result_shows_error(
    release_page: ReleaseSelectionPage,
    session: WizardSession,
) -> None:
    session.set_selected_release(_sample_release())
    release_page.apply_release_fetch_result(
        ReleaseFetchResult(error="Unable to reach MusicBrainz.")
    )

    assert session.selected_release is None
    assert release_page.isComplete() is False
    assert "Unable to reach MusicBrainz" in release_page._status_label.text()
    assert release_page._track_table.rowCount() == 0


def test_release_selection_fetches_tracks_in_background(
    qtbot,
    container,
    session,
    musicbrainz_client: MagicMock,
) -> None:
    session.search_results = [_sample_summary()]
    musicbrainz_client.get_release.return_value = _sample_release()

    page = ReleaseSelectionPage(container, musicbrainz_client=musicbrainz_client)
    qtbot.addWidget(page)
    page.initializePage()

    item = page.release_list.item(0)
    page.release_list.setCurrentItem(item)
    qtbot.waitUntil(lambda: page._track_table.rowCount() == 2, timeout=2000)

    musicbrainz_client.get_release.assert_called_once_with("release-mbid-1")
    assert page.session.selected_release is not None
    assert page._progress_bar.isVisible() is False


def test_initialize_displays_existing_selected_release(
    release_page: ReleaseSelectionPage,
    session: WizardSession,
) -> None:
    session.search_results = [_sample_summary()]
    session.set_selected_release(_sample_release())

    release_page.initializePage()

    assert release_page.release_list.currentItem() is not None
    assert release_page._track_table.rowCount() == 2
    assert release_page.isComplete() is True



