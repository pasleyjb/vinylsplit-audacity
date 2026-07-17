"""Welcome wizard page."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import ClassVar

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QWizardPage,
)

from vinylsplit.audacity.client import AudacityClient, AudacityError
from vinylsplit.audacity.connection import (
    AudacityConnectionResult,
    verify_audacity_connection,
)
from vinylsplit.audacity.import_audio import (
    import_audio_file,
    probe_audacity_project,
    seed_queries_from_track_names,
)
from vinylsplit.core.container import Container
from vinylsplit.metadata.local_tags import (
    AUDIO_FILE_FILTER,
    LocalAudioTags,
    read_local_audio_tags,
)
from vinylsplit.wizard.pages.base import WizardPageBase
from vinylsplit.wizard.pages.page_ids import PageId
from vinylsplit.wizard.ui_style import (
    connection_status_text,
    create_section_group,
    create_status_label,
    style_primary_button,
    style_secondary_button,
)

_logger = logging.getLogger(__name__)

_STATUS_CONNECTED = connection_status_text(connected=True)
_STATUS_NOT_CONNECTED = connection_status_text(connected=False)


class _ConnectionWorker(QThread):
    """Run Audacity verification off the UI thread."""

    finished = Signal(object)

    def __init__(
        self,
        verifier: Callable[[], AudacityConnectionResult],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._verifier = verifier

    def run(self) -> None:
        self.finished.emit(self._verifier())


class _ImportWorker(QThread):
    """Import audio into Audacity off the UI thread."""

    finished = Signal(object)

    def __init__(
        self,
        importer: Callable[[], str],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._importer = importer

    def run(self) -> None:
        try:
            message = self._importer()
            self.finished.emit((True, message))
        except Exception as exc:  # noqa: BLE001 — surface to UI
            self.finished.emit((False, str(exc)))


class WelcomePage(WizardPageBase):
    """Introduce the application and outline the digitization workflow."""

    PAGE_ID: ClassVar[int] = PageId.OPEN
    PAGE_TITLE: ClassVar[str] = "Open album"
    PAGE_SUBTITLE: ClassVar[str] = (
        "Open your vinyl capture and connect to Audacity, then continue."
    )

    def __init__(
        self,
        container: Container,
        parent: QWizardPage | None = None,
        *,
        connection_verifier: Callable[[], AudacityConnectionResult] | None = None,
        tag_reader: Callable[[Path], LocalAudioTags] | None = None,
        audio_importer: Callable[[Path], None] | None = None,
        project_prober: Callable[[], tuple[str, str]] | None = None,
    ) -> None:
        self._connection_verifier = connection_verifier or verify_audacity_connection
        self._tag_reader = tag_reader or read_local_audio_tags
        self._audio_importer = audio_importer
        self._project_prober = project_prober
        self._connection_worker: _ConnectionWorker | None = None
        self._import_worker: _ImportWorker | None = None
        super().__init__(container, parent)

    def build_content(self) -> None:
        self._layout.addWidget(
            self._create_info_banner(
                "<b>Open album</b><br><br>"
                "1. Open your capture file (tags seed MusicBrainz)<br>"
                "2. Connect to Audacity (imports the file when connected)<br>"
                "3. Click <b>Next</b> to find the release"
            )
        )

        self._layout.addWidget(self._build_source_file_section())
        self._layout.addWidget(self._build_audacity_connection_section())

    def _build_source_file_section(self) -> QWidget:
        """Build the local audio file picker and tag preview."""
        section = create_section_group("Source Audio")
        layout = QVBoxLayout(section)
        layout.setSpacing(10)

        self._file_label = create_status_label(tone="muted")
        self._file_label.setText("No audio file selected.")
        self._file_label.setWordWrap(True)
        self._file_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self._tags_label = QLabel("")
        self._tags_label.setWordWrap(True)
        self._tags_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        buttons = QHBoxLayout()
        self._browse_button = QPushButton()
        style_primary_button(self._browse_button, "Open Audio File…")
        self._browse_button.clicked.connect(self._on_browse_clicked)

        self._clear_file_button = QPushButton()
        style_secondary_button(self._clear_file_button, "Clear")
        self._clear_file_button.clicked.connect(self._on_clear_file_clicked)
        self._clear_file_button.setEnabled(False)

        buttons.addWidget(self._browse_button)
        buttons.addWidget(self._clear_file_button)
        buttons.addStretch()

        layout.addWidget(self._file_label)
        layout.addWidget(self._tags_label)
        layout.addLayout(buttons)
        return section

    def _build_audacity_connection_section(self) -> QWidget:
        """Build the Audacity connection status and controls."""
        section = create_section_group("Audacity Connection")
        layout = QVBoxLayout(section)
        layout.setSpacing(10)

        self._status_label = create_status_label(tone="neutral")
        self._status_label.setText(_STATUS_NOT_CONNECTED)

        self._connect_button = QPushButton()
        style_primary_button(self._connect_button, "Connect")
        self._connect_button.clicked.connect(self._on_connect_clicked)

        self._message_label = QLabel("")
        self._message_label.setWordWrap(True)
        self._message_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        layout.addWidget(self._status_label)
        layout.addWidget(self._connect_button)
        layout.addWidget(self._message_label)
        return section

    def _on_browse_clicked(self) -> None:
        """Let the user pick a capture file and seed search from its tags."""
        start_dir = self._default_open_directory()

        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Open vinyl capture",
            start_dir,
            AUDIO_FILE_FILTER,
        )
        if not path_str:
            return

        self.apply_source_file(Path(path_str))

    def _default_open_directory(self) -> str:
        """Return the sticky last-open folder (directory only, not a file)."""
        # Prefer the folder of a file chosen this session.
        if self.session.source_audio_path is not None:
            parent = self.session.source_audio_path.parent
            if parent.is_dir():
                return str(parent)

        settings = self.container.settings
        stored = settings.get(settings.KEY_LAST_OPEN_DIR, "")
        if isinstance(stored, str) and stored:
            candidate = Path(stored).expanduser()
            if candidate.is_dir():
                return str(candidate)

        return str(Path.home())

    def _remember_open_directory(self, path: Path) -> None:
        """Persist the directory of *path* for the next open dialog."""
        directory = path.expanduser().resolve().parent
        if not directory.is_dir():
            return
        settings = self.container.settings
        settings.set(settings.KEY_LAST_OPEN_DIR, str(directory))
        settings.sync()

    def _on_clear_file_clicked(self) -> None:
        self.session.clear_source_audio()
        self._refresh_source_file_ui()

    def apply_source_file(self, path: Path) -> None:
        """Load tags from *path* into the session (also used in tests)."""
        try:
            tags = self._tag_reader(path)
        except (OSError, ValueError) as exc:
            self._file_label.setText(f"Could not open file: {exc}")
            self._tags_label.setText("")
            self.session.add_validation_error(str(exc))
            return

        self.session.set_source_audio(tags.path, tags, seed_source="file")
        self._remember_open_directory(tags.path)
        self.session.clear_validation_errors()
        self._refresh_source_file_ui()
        _logger.info(
            "Source audio selected: %s (artist=%r album=%r source=%s)",
            tags.path,
            tags.search_artist,
            tags.search_album,
            tags.source,
        )

        # If already connected, import into Audacity in the background.
        if self.session.audacity_connected and not self.session.audio_imported_to_audacity:
            self._start_import(tags.path)

    def _refresh_source_file_ui(self) -> None:
        path = self.session.source_audio_path
        tags = self.session.local_tags
        if path is None:
            self._file_label.setText("No audio file selected.")
            self._tags_label.setText(
                "Open a capture to seed MusicBrainz from embedded tags "
                "(or filename). VinylSplit can also import it into Audacity "
                "when you connect."
            )
            self._clear_file_button.setEnabled(False)
            return

        self._file_label.setText(f"File: {path}")
        self._clear_file_button.setEnabled(True)

        if tags is None:
            self._tags_label.setText("No tag data available.")
            return

        lines = [
            f"<b>Detected:</b> {tags.summary_line()}",
            f"Tag source: {tags.source}",
        ]
        if tags.year:
            lines.append(f"Year: {tags.year}")
        if tags.musicbrainz_album_id:
            lines.append(f"MusicBrainz release ID: {tags.musicbrainz_album_id}")
        if not tags.has_search_seed:
            lines.append(
                "No artist/album tags found — you can still enter them on the "
                "next page."
            )
        else:
            lines.append(
                "These values will prefill the MusicBrainz search on the next page."
            )
        self._tags_label.setText("<br>".join(lines))

    def _on_connect_clicked(self) -> None:
        """Start an Audacity connectivity check."""
        if self._connection_worker is not None and self._connection_worker.isRunning():
            return

        self._connect_button.setEnabled(False)
        self._message_label.setText("Connecting to Audacity...")
        self._update_status_label(connected=False)

        self._connection_worker = _ConnectionWorker(self._connection_verifier, self)
        self._connection_worker.finished.connect(self._on_connection_finished)
        self._connection_worker.start()

    def _on_connection_finished(self, result: AudacityConnectionResult) -> None:
        """Apply the connectivity result to the page UI."""
        self._connect_button.setEnabled(True)
        self._connection_worker = None
        self.apply_connection_result(result)

    def initializePage(self) -> None:
        super().initializePage()
        self._update_status_label(connected=self.session.audacity_connected)
        self._refresh_source_file_ui()

    def apply_connection_result(self, result: AudacityConnectionResult) -> None:
        """Update UI labels from a connectivity result (also used in tests)."""
        self.session.set_audacity_connected(result.success)
        self._update_status_label(connected=result.success)
        self._message_label.setText(result.message)

        if result.success:
            self.session.clear_validation_errors()
            _logger.info("Audacity connection verified: %s", result.message)
            self._after_successful_connect()
        else:
            self.session.add_validation_error(result.message)
            _logger.warning("Audacity connection failed: %s", result.message)

    def _after_successful_connect(self) -> None:
        """Import chosen file and/or seed search from the open Audacity project."""
        path = self.session.source_audio_path
        if path is not None and not self.session.audio_imported_to_audacity:
            self._start_import(path)
            return

        # No local file — try weak seed from Audacity track names.
        if not self.session.last_artist_query and not self.session.last_album_query:
            self._try_seed_from_audacity()

    def _start_import(self, path: Path) -> None:
        if self._import_worker is not None and self._import_worker.isRunning():
            return

        self._message_label.setText(f"Importing into Audacity: {path.name}…")
        self._import_worker = _ImportWorker(lambda: self._run_import(path), self)
        self._import_worker.finished.connect(self._on_import_finished)
        self._import_worker.start()

    def _run_import(self, path: Path) -> str:
        if self._audio_importer is not None:
            self._audio_importer(path)
        else:
            client = self.container.resolve("audacity")
            assert isinstance(client, AudacityClient)
            client.connect()
            try:
                import_audio_file(client, path)
            finally:
                client.disconnect()
        self.session.mark_audio_imported()
        return f"Imported into Audacity: {path.name}"

    def _on_import_finished(self, result: object) -> None:
        self._import_worker = None
        success, message = result  # type: ignore[misc]
        if success:
            base = (
                "Connected to Audacity."
                if self.session.audacity_connected
                else ""
            )
            combined = f"{base} {message}".strip()
            self._message_label.setText(combined)
            _logger.info("%s", message)
        else:
            self._message_label.setText(
                f"Connected, but import failed: {message}. "
                "Open the file in Audacity manually if needed."
            )
            self.session.add_validation_error(str(message))
            _logger.warning("Audacity import failed: %s", message)

    def _try_seed_from_audacity(self) -> None:
        """Prefill search from Audacity track names when possible."""
        try:
            if self._project_prober is not None:
                artist, album = self._project_prober()
            else:
                client = self.container.resolve("audacity")
                assert isinstance(client, AudacityClient)
                client.connect()
                try:
                    probe = probe_audacity_project(client)
                    artist, album = seed_queries_from_track_names(probe.track_names)
                finally:
                    client.disconnect()
        except (AudacityError, OSError, TypeError, ValueError) as exc:
            _logger.debug("Audacity project probe failed: %s", exc)
            return

        if not artist and not album:
            return

        self.session.set_search_seed(artist=artist, album=album, seed_source="audacity")
        self._message_label.setText(
            f"{self._message_label.text()} "
            f"Seeded search from Audacity track name: "
            f"{artist or '—'} / {album or '—'}."
        )
        _logger.info("Seeded search from Audacity: artist=%r album=%r", artist, album)

    def _update_status_label(self, *, connected: bool) -> None:
        self._status_label.setText(
            _STATUS_CONNECTED if connected else _STATUS_NOT_CONNECTED
        )
        self._status_label.setObjectName(
            "StatusSuccess" if connected else "StatusError"
        )
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

    def is_audacity_connected(self) -> bool:
        """Return whether Audacity communication is available."""
        return self.session.audacity_connected
