"""Tests for the Welcome wizard page."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from vinylsplit.audacity.connection import AudacityConnectionResult
from vinylsplit.metadata.local_tags import LocalAudioTags
from vinylsplit.wizard.pages.welcome_page import (
    _STATUS_CONNECTED,
    _STATUS_NOT_CONNECTED,
    WelcomePage,
)


def _isolated_page(
    container,
    *,
    verifier=None,
    tag_reader=None,
    audio_importer=None,
    project_prober=None,
) -> WelcomePage:
    """Welcome page that never talks to a real Audacity instance."""
    return WelcomePage(
        container,
        connection_verifier=verifier
        or (lambda: AudacityConnectionResult(True, "Connected to Audacity 3.x")),
        tag_reader=tag_reader,
        audio_importer=audio_importer or (lambda _p: None),
        project_prober=project_prober or (lambda: ("", "")),
    )


@pytest.fixture
def welcome_page(container) -> WelcomePage:
    """Provide a welcome page with a synchronous connection verifier."""
    page = _isolated_page(container)
    page.show()
    return page


def test_welcome_page_shows_not_connected_initially(container) -> None:
    page = _isolated_page(
        container,
        verifier=lambda: AudacityConnectionResult(False, ""),
    )

    assert page._status_label.text() == _STATUS_NOT_CONNECTED
    assert page.is_audacity_connected() is False
    assert page._connect_button.text() == "Connect"
    assert page._browse_button is not None


def test_apply_connection_result_success(
    welcome_page: WelcomePage, session
) -> None:
    welcome_page.apply_connection_result(
        AudacityConnectionResult(success=True, message="Connected to Audacity 3.x")
    )

    assert welcome_page._status_label.text() == _STATUS_CONNECTED
    assert welcome_page._message_label.text().startswith("Connected to Audacity 3.x")
    assert welcome_page.is_audacity_connected() is True
    assert session.audacity_connected is True
    assert session.validation_errors == []


def test_apply_connection_result_failure(container, session) -> None:
    page = _isolated_page(
        container,
        verifier=lambda: AudacityConnectionResult(False, ""),
    )

    page.apply_connection_result(
        AudacityConnectionResult(success=False, message="Pipes are not available.")
    )

    assert page._status_label.text() == _STATUS_NOT_CONNECTED
    assert page._message_label.text() == "Pipes are not available."
    assert page.is_audacity_connected() is False
    assert session.audacity_connected is False
    assert "Pipes are not available." in session.validation_errors


def test_connect_button_updates_ui(qtbot, container) -> None:
    results = [
        AudacityConnectionResult(success=True, message="Connected to Audacity 3.x"),
    ]

    page = _isolated_page(container, verifier=lambda: results.pop(0))
    qtbot.addWidget(page)

    qtbot.mouseClick(page._connect_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: page._status_label.text() == _STATUS_CONNECTED, timeout=2000
    )

    assert page._message_label.text().startswith("Connected to Audacity 3.x")
    assert page.is_audacity_connected() is True
    assert page._connect_button.isEnabled() is True


def test_connect_button_shows_error_message(qtbot, container) -> None:
    page = _isolated_page(
        container,
        verifier=lambda: AudacityConnectionResult(
            success=False,
            message="Audacity mod-script-pipe endpoints are not available.",
        ),
    )
    qtbot.addWidget(page)

    qtbot.mouseClick(page._connect_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: "not available" in page._message_label.text(),
        timeout=2000,
    )

    assert page._status_label.text() == _STATUS_NOT_CONNECTED
    assert page.is_audacity_connected() is False


def test_apply_source_file_seeds_session(container, session, tmp_path: Path) -> None:
    path = tmp_path / "Pink Floyd - Animals.flac"
    path.write_bytes(b"x")

    def reader(p: Path) -> LocalAudioTags:
        return LocalAudioTags(
            path=p,
            artist="Pink Floyd",
            album="Animals",
            source="tags",
        )

    page = _isolated_page(container, tag_reader=reader)
    page.show()
    page.apply_source_file(path)

    assert session.source_audio_path == path
    assert session.last_artist_query == "Pink Floyd"
    assert session.last_album_query == "Animals"
    assert "Pink Floyd" in page._tags_label.text()
    assert page._clear_file_button.isEnabled() is True
    # Directory (not filename) is sticky for the next open dialog
    assert page._default_open_directory() == str(path.parent)
    assert container.settings.get(container.settings.KEY_LAST_OPEN_DIR) == str(
        path.resolve().parent
    )


def test_default_open_directory_uses_sticky_setting(
    container, session, tmp_path: Path
) -> None:
    sticky = tmp_path / "captures"
    sticky.mkdir()
    container.settings.set(container.settings.KEY_LAST_OPEN_DIR, str(sticky))

    page = _isolated_page(container)
    assert page._default_open_directory() == str(sticky)


def test_apply_connection_imports_selected_file(
    qtbot, container, session, tmp_path: Path
) -> None:
    path = tmp_path / "capture.wav"
    path.write_bytes(b"x")
    imported: list[Path] = []

    def reader(p: Path) -> LocalAudioTags:
        return LocalAudioTags(path=p, artist="A", album="B", source="tags")

    page = _isolated_page(
        container,
        tag_reader=reader,
        audio_importer=lambda p: imported.append(p),
    )
    qtbot.addWidget(page)
    page.apply_source_file(path)
    page.apply_connection_result(
        AudacityConnectionResult(success=True, message="Connected to Audacity 3.x")
    )
    qtbot.waitUntil(lambda: session.audio_imported_to_audacity is True, timeout=2000)

    assert imported == [path]
    assert "Imported" in page._message_label.text()


def test_connect_seeds_from_audacity_when_no_file(container, session) -> None:
    page = _isolated_page(
        container,
        project_prober=lambda: ("Miles Davis", "Kind of Blue"),
    )
    page.show()
    page.apply_connection_result(
        AudacityConnectionResult(success=True, message="Connected to Audacity 3.x")
    )

    assert session.last_artist_query == "Miles Davis"
    assert session.last_album_query == "Kind of Blue"
    assert session.metadata_seed_source == "audacity"
    assert "Miles Davis" in page._message_label.text()
