"""Tests for waveform integration on the generate layout page."""

from __future__ import annotations

from pathlib import Path

from vinylsplit.labels.layout_engine import AlbumLayout, TrackRegion
from vinylsplit.metadata.models import Artist, Medium, Release, Track
from vinylsplit.waveform.peaks import PeakOverview
from vinylsplit.wizard.pages.generate_album_layout_page import GenerateAlbumLayoutPage


def _sample_release() -> Release:
    return Release(
        id="r1",
        title="Album",
        artist=Artist(id="a1", name="Artist"),
        date="1970",
        country="US",
        release_year="1970",
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
                        id="t1",
                        title="One",
                        position=1,
                        number="1",
                        length_ms=60_000,
                    ),
                    Track(
                        id="t2",
                        title="Two",
                        position=2,
                        number="2",
                        length_ms=90_000,
                    ),
                ),
            ),
        ),
    )


def test_layout_changed_commits_session(container, session) -> None:
    session.set_selected_release(_sample_release())
    empty = PeakOverview(
        path=Path("/tmp/x.wav"),
        duration_seconds=200.0,
        sample_rate=8000,
        mins=tuple(0.0 for _ in range(50)),
        maxs=tuple(0.1 for _ in range(50)),
        source="wave",
    )
    page = GenerateAlbumLayoutPage(container, peak_loader=lambda _p: empty)
    page.show()
    session.source_audio_path = Path("/tmp/x.wav")
    page.initializePage()

    edited = AlbumLayout(
        release_id="r1",
        artist_name="Artist",
        album_title="Album",
        regions=(
            TrackRegion(0, "01", "One", "01 One", 25.0, 85.0),
            TrackRegion(1, "02", "Two", "02 Two", 85.0, 175.0),
        ),
    )
    page._on_layout_changed(edited)

    assert session.album_layout is not None
    assert session.album_layout.regions[0].start_seconds == 25.0
    assert session.layout_offset_seconds == 25.0
    assert page._preview_table.item(0, 2).text().startswith("00:25")


def test_layout_preview_does_not_commit(container, session) -> None:
    session.set_selected_release(_sample_release())
    page = GenerateAlbumLayoutPage(container)
    page.show()
    page.initializePage()

    preview = AlbumLayout(
        release_id="r1",
        artist_name="Artist",
        album_title="Album",
        regions=(
            TrackRegion(0, "01", "One", "01 One", 40.0, 100.0),
            TrackRegion(1, "02", "Two", "02 Two", 100.0, 190.0),
        ),
    )
    page._on_layout_preview(preview)

    assert session.album_layout is not None
    assert session.album_layout.regions[0].start_seconds == 0.0
    assert page._preview_table.item(0, 2).text().startswith("00:40")
