"""Tests for the strongly typed wizard session state."""

from __future__ import annotations

from pathlib import Path

from vinylsplit.metadata.models import (
    Artist,
    Medium,
    Release,
    Track,
)
from vinylsplit.metadata.session import AlbumArtwork, ExportFormat, WizardSession


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


def test_default_session_fields() -> None:
    session = WizardSession()

    assert session.audacity_connected is False
    assert session.selected_release is None
    assert session.album_artwork is None
    assert session.track_list == []
    assert session.album_layout is None
    assert session.initial_regions_generated is False
    assert session.layout_review_refreshed is False
    assert session.regions_created_count == 0
    assert session.export_format is None
    assert session.output_directory is None
    assert session.recording_already_completed is False
    assert session.validation_errors == []
    assert session.search_results == []
    assert session.last_artist_query == ""
    assert session.last_album_query == ""
    assert session.source_audio_path is None
    assert session.local_tags is None
    assert session.audio_imported_to_audacity is False
    assert session.metadata_seed_source == ""


def test_set_audacity_connected() -> None:
    session = WizardSession()

    session.set_audacity_connected(True)
    assert session.audacity_connected is True

    session.set_audacity_connected(False)
    assert session.audacity_connected is False


def test_set_layout_transform_offset() -> None:
    session = WizardSession()
    session.set_selected_release(_sample_release())
    assert session.album_layout is not None
    base_end = session.album_layout.regions[0].end_seconds

    session.set_layout_transform(offset_seconds=30.0)

    assert session.layout_offset_seconds == 30.0
    assert session.album_layout is not None
    assert session.album_layout.regions[0].start_seconds == 30.0
    assert session.album_layout.regions[0].end_seconds == base_end + 30.0
    assert session.initial_regions_generated is False


def test_set_edited_layout() -> None:
    from vinylsplit.labels.layout_engine import AlbumLayout, TrackRegion

    session = WizardSession()
    session.set_selected_release(_sample_release())
    edited = AlbumLayout(
        release_id="x",
        artist_name="A",
        album_title="B",
        regions=(
            TrackRegion(0, "01", "One", "01 One", 12.0, 50.0),
            TrackRegion(1, "02", "Two", "02 Two", 50.0, 90.0),
        ),
    )
    session.set_edited_layout(edited)

    assert session.album_layout is edited
    assert session.layout_offset_seconds == 12.0
    assert session.initial_regions_generated is False


def test_mark_using_existing_regions() -> None:
    session = WizardSession()
    session.mark_using_existing_regions(5)

    assert session.skipped_region_generation is True
    assert session.initial_regions_generated is True
    assert session.layout_review_refreshed is True
    assert session.regions_created_count == 5
    assert session.ready_for_export() is True


def test_set_source_audio_seeds_search() -> None:
    from vinylsplit.metadata.local_tags import LocalAudioTags

    session = WizardSession()
    path = Path("/tmp/capture.flac")
    tags = LocalAudioTags(
        path=path,
        artist="Miles Davis",
        album="Kind of Blue",
        source="tags",
    )

    session.set_source_audio(path, tags, seed_source="file")

    assert session.source_audio_path == path
    assert session.local_tags is tags
    assert session.last_artist_query == "Miles Davis"
    assert session.last_album_query == "Kind of Blue"
    assert session.metadata_seed_source == "file"
    assert session.audio_imported_to_audacity is False

    session.mark_audio_imported()
    assert session.audio_imported_to_audacity is True


def test_set_selected_release_populates_track_list_and_layout() -> None:
    session = WizardSession()
    release = _sample_release()

    session.set_selected_release(release)

    assert session.selected_release is release
    assert len(session.track_list) == 2
    assert session.track_list[0].title == "Speak to Me"
    assert session.album_layout is not None
    assert session.album_layout.track_count == 2
    assert session.album_layout.regions[0].start_seconds == 0.0
    assert session.album_layout.regions[0].end_seconds == 90.0
    assert session.album_layout.regions[1].start_seconds == 90.0
    assert session.album_layout.regions[1].end_seconds == 253.0
    assert session.initial_regions_generated is False


def test_set_selected_release_clears_layout_workflow_state() -> None:
    session = WizardSession()
    session.set_selected_release(_sample_release())
    session.mark_initial_regions_generated(2)
    session.mark_layout_review_refreshed()

    session.set_selected_release(_sample_release())

    assert session.initial_regions_generated is False
    assert session.layout_review_refreshed is False
    assert session.regions_created_count == 0


def test_clear_selected_release() -> None:
    session = WizardSession()
    session.set_selected_release(_sample_release())
    session.set_album_artwork(AlbumArtwork(data=b"cover", mime_type="image/jpeg"))
    session.mark_initial_regions_generated(2)

    session.clear_selected_release()

    assert session.selected_release is None
    assert session.album_artwork is None
    assert session.track_list == []
    assert session.album_layout is None
    assert session.initial_regions_generated is False


def test_album_artwork_availability() -> None:
    empty = AlbumArtwork()
    populated = AlbumArtwork(data=b"png-bytes", mime_type="image/png")

    assert empty.is_available is False
    assert populated.is_available is True


def test_export_format_and_output_directory() -> None:
    session = WizardSession()
    output_dir = Path("/tmp/vinylsplit")

    session.set_export_format(ExportFormat.FLAC)
    session.set_output_directory(output_dir)

    assert session.export_format is ExportFormat.FLAC
    assert session.output_directory == output_dir


def test_recording_already_completed() -> None:
    session = WizardSession()

    session.set_recording_already_completed(True)
    assert session.recording_already_completed is True


def test_validation_errors_deduplicated() -> None:
    session = WizardSession()

    session.add_validation_error("First error")
    session.add_validation_error("First error")
    session.add_validation_error("Second error")

    assert session.validation_errors == ["First error", "Second error"]
    assert session.has_validation_errors() is True

    session.clear_validation_errors()
    assert session.validation_errors == []
    assert session.has_validation_errors() is False


def test_ready_for_export_after_regions_written() -> None:
    session = WizardSession()
    session.set_selected_release(_sample_release())

    assert session.ready_for_export() is False

    session.mark_initial_regions_generated(2)
    assert session.ready_for_export() is True


def test_has_selected_release() -> None:
    session = WizardSession()

    assert session.has_selected_release() is False

    session.set_selected_release(_sample_release())
    assert session.has_selected_release() is True


def test_layout_generation_timer_tracks_elapsed_time() -> None:
    session = WizardSession()

    assert session.layout_generation_elapsed_seconds() is None

    session.start_layout_generation()
    session.mark_initial_regions_generated(2)

    elapsed = session.layout_generation_elapsed_seconds()
    assert elapsed is not None
    assert elapsed >= 0