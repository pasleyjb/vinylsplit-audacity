"""Tests for the Finish wizard page."""

from __future__ import annotations

from pathlib import Path

from vinylsplit.export.models import AlbumExportResult
from vinylsplit.metadata.session import ExportFormat
from vinylsplit.metadata.models import (
    Artist,
    Medium,
    Release,
    Track,
)
from vinylsplit.wizard.pages.finish_page import FinishPage


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
                        length_ms=90000,
                    ),
                    Track(
                        id="track-2",
                        title="Breathe",
                        position=2,
                        number="2",
                        length_ms=163000,
                    ),
                ),
            ),
        ),
    )


def test_finish_page_reports_layout_summary(container, session) -> None:
    session.set_selected_release(_sample_release())
    session.start_layout_generation()
    session.mark_initial_regions_generated(2)
    session.mark_layout_review_refreshed()

    page = FinishPage(container, prefetch_artwork=False)
    page.initializePage()

    summary = page._summary_label.text()
    assert "Pink Floyd" in summary
    assert "The Dark Side of the Moon" in summary
    assert "Regions created:</b> 2" in summary
    assert "Export Tracks" in summary or "Choose a format" in summary


def test_selected_export_format_reads_combo_string_data(
    container, session, qapp
) -> None:
    page = FinishPage(container, prefetch_artwork=False)
    page.show()
    page._format_combo.clear()
    page._format_combo.addItem("FLAC", "flac")

    assert page._selected_export_format() is ExportFormat.FLAC


def test_apply_export_result_updates_session(container, session) -> None:
    session.set_selected_release(_sample_release())
    session.mark_initial_regions_generated(2)
    session.mark_layout_review_refreshed()
    session.set_output_directory(Path("/tmp/vinylsplit"))
    session.set_export_format(ExportFormat.FLAC)

    page = FinishPage(container, prefetch_artwork=False)
    page.apply_export_result(
        AlbumExportResult(
            success=True,
            message="Exported 2 track(s).",
            tracks_exported=2,
            output_directory=Path("/tmp/vinylsplit"),
        )
    )

    assert session.export_completed is True
    assert session.exported_track_count == 2