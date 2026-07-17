"""Finish wizard page."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import ClassVar

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QWizard,
    QWizardPage,
    QWidget,
)

from vinylsplit.audacity.client import AudacityClient
from vinylsplit.core.container import Container
from vinylsplit.export.artwork import ArtworkFetchResult, fetch_release_artwork
from vinylsplit.export.engine import ExportEngine
from vinylsplit.export.formats import resolve_export_format
from vinylsplit.export.models import AlbumExportResult, ExportSettings
from vinylsplit.metadata.session import ExportFormat
from vinylsplit.wizard.pages.base import WizardPageBase
from vinylsplit.wizard.pages.page_ids import PageId
from vinylsplit.wizard.ui_style import (
    artwork_preview_pixmap,
    build_artwork_preview_panel,
    create_section_group,
    create_status_label,
    finish_button_label,
    style_primary_button,
    style_secondary_button,
)

_logger = logging.getLogger(__name__)


class _ArtworkFetchWorker(QThread):
    """Fetch album artwork off the UI thread."""

    finished = Signal(object)

    def __init__(
        self,
        fetcher: Callable[[str], ArtworkFetchResult],
        release_id: str,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._fetcher = fetcher
        self._release_id = release_id

    def run(self) -> None:
        self.finished.emit(self._fetcher(self._release_id))


class _ExportWorker(QThread):
    """Run album export off the UI thread."""

    progress = Signal(int, int)
    finished = Signal(object)

    def __init__(
        self,
        exporter: Callable[[Callable[[int, int], None] | None], AlbumExportResult],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._exporter = exporter

    def run(self) -> None:
        self.finished.emit(self._exporter(self.progress.emit))


class FinishPage(WizardPageBase):
    """Export tagged tracks using the final Audacity region layout."""

    PAGE_ID: ClassVar[int] = PageId.EXPORT
    PAGE_TITLE: ClassVar[str] = "Export"
    PAGE_SUBTITLE: ClassVar[str] = (
        "Final approval — export tagged tracks, or start a new album."
    )

    def __init__(
        self,
        container: Container,
        parent: QWizardPage | None = None,
        *,
        audacity_client: AudacityClient | None = None,
        artwork_fetcher: Callable[[str], ArtworkFetchResult] | None = None,
        album_exporter: Callable[
            [Callable[[int, int], None] | None], AlbumExportResult
        ]
        | None = None,
        prefetch_artwork: bool = True,
    ) -> None:
        self._audacity = audacity_client
        self._artwork_fetcher = artwork_fetcher
        self._album_exporter = album_exporter
        self._prefetch_artwork = prefetch_artwork
        self._artwork_worker: _ArtworkFetchWorker | None = None
        self._export_worker: _ExportWorker | None = None
        super().__init__(container, parent)

    def build_content(self) -> None:
        self._summary_label = self._create_info_banner("")
        self._layout.addWidget(self._summary_label)

        content_row = QWidget()
        content_layout = QHBoxLayout(content_row)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        export_group = create_section_group("Export Settings")
        form = QFormLayout(export_group)
        form.setSpacing(10)

        self._format_combo = QComboBox()
        for export_format in ExportFormat:
            self._format_combo.addItem(export_format.value.upper(), export_format)
        flac_index = self._format_combo.findData(ExportFormat.FLAC)
        if flac_index >= 0:
            self._format_combo.setCurrentIndex(flac_index)
        form.addRow("Format:", self._format_combo)

        self._output_path_label = QLabel("Not selected")
        self._output_path_label.setWordWrap(True)
        self._browse_button = QPushButton()
        style_secondary_button(self._browse_button, "Choose Folder…")
        self._browse_button.clicked.connect(self._on_browse_clicked)
        output_row = QWidget()
        output_layout = QHBoxLayout(output_row)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.addWidget(self._output_path_label, stretch=1)
        output_layout.addWidget(self._browse_button)
        form.addRow("Output folder:", output_row)

        self._hint_label = create_status_label(tone="muted")
        self._hint_label.setText(
            "Choose a format and output folder. Tracks are saved in an album "
            "subfolder with cover art, then press Export Tracks or Finish."
        )
        form.addRow(self._hint_label)

        content_layout.addWidget(export_group, stretch=1)

        artwork_panel, image_label, caption_label = build_artwork_preview_panel()
        self._artwork_panel = artwork_panel
        self._artwork_image_label = image_label
        self._artwork_caption_label = caption_label
        content_layout.addWidget(artwork_panel)

        self._layout.addWidget(content_row)

        action_row = QHBoxLayout()
        self._export_button = QPushButton()
        style_primary_button(self._export_button, "Export Tracks")
        self._export_button.clicked.connect(self._on_export_clicked)
        action_row.addWidget(self._export_button)

        self._new_album_button = QPushButton()
        style_secondary_button(self._new_album_button, "Open new album")
        self._new_album_button.setToolTip(
            "Clear this session and return to Open album for the next record."
        )
        self._new_album_button.clicked.connect(self._on_new_album_clicked)
        action_row.addWidget(self._new_album_button)
        action_row.addStretch()
        self._layout.addLayout(action_row)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        self._layout.addWidget(self._progress_bar)

        self._status_label = create_status_label()
        self._layout.addWidget(self._status_label)

    @property
    def audacity(self) -> AudacityClient:
        if self._audacity is None:
            self._audacity = self.container.resolve("audacity")
        return self._audacity

    def initializePage(self) -> None:
        super().initializePage()
        self._restore_export_settings()
        self._update_summary()
        self._update_artwork_preview()
        if self._prefetch_artwork:
            self._prefetch_artwork_async()
        self._update_wizard_finish_button()
        self.completeChanged.emit()

    def cleanupPage(self) -> None:
        if self._artwork_worker is not None and self._artwork_worker.isRunning():
            self._artwork_worker.wait(2000)
        if self._export_worker is not None and self._export_worker.isRunning():
            self._export_worker.wait(5000)
        super().cleanupPage()

    def isComplete(self) -> bool:
        return self.session.ready_for_export()

    def validatePage(self) -> bool:
        """Run export when the wizard Finish button is pressed."""
        if self.session.export_completed:
            return True
        return self._run_export(show_progress=False)

    def _restore_export_settings(self) -> None:
        if self.session.export_format is not None:
            index = self._format_combo.findData(self.session.export_format)
            if index >= 0:
                self._format_combo.setCurrentIndex(index)
        if self.session.output_directory is not None:
            self._output_path_label.setText(str(self.session.output_directory))

    def _update_summary(self) -> None:
        release = self.session.selected_release
        regions_created = self.session.regions_created_count
        elapsed = self.session.layout_generation_elapsed_seconds()

        if release is None:
            self._summary_label.setText(
                "<b>All Done!</b><br><br>"
                "No release was selected during this session."
            )
            self._hint_label.setVisible(False)
            return

        elapsed_text = "—"
        if elapsed is not None:
            elapsed_text = f"{elapsed:.1f} seconds"

        export_note = (
            "Choose a format and output folder, then press <b>Export Tracks</b> "
            "or <b>Finish</b>."
        )
        if self.session.export_completed:
            export_note = (
                f"Exported <b>{self.session.exported_track_count}</b> track(s) "
                "with embedded metadata and artwork."
            )
            self._hint_label.setVisible(False)
        else:
            self._hint_label.setVisible(True)

        self._summary_label.setText(
            "<b>Final approval &amp; export</b><br><br>"
            f"<b>Artist:</b> {release.artist_name}<br>"
            f"<b>Album:</b> {release.title}<br>"
            f"<b>Regions:</b> {regions_created}<br>"
            f"<b>Layout generation time:</b> {elapsed_text}<br><br>"
            f"{export_note}"
        )

    def _update_artwork_preview(self) -> None:
        artwork = self.session.album_artwork
        if artwork is not None and artwork.is_available and artwork.data:
            pixmap = artwork_preview_pixmap(artwork.data)
            if not pixmap.isNull():
                self._artwork_image_label.setPixmap(pixmap)
                self._artwork_image_label.setText("")
                self._set_artwork_caption(
                    "Album artwork is ready for embedding.",
                    tone="success",
                )
                return

        self._artwork_image_label.clear()
        self._artwork_image_label.setText("No artwork yet")
        self._set_artwork_caption(
            "Album artwork will be downloaded from Cover Art Archive during export.",
            tone="muted",
        )

    def _set_artwork_caption(self, text: str, *, tone: str) -> None:
        self._artwork_caption_label.setText(text)
        object_name = {
            "success": "StatusSuccess",
            "error": "StatusError",
            "neutral": "StatusNeutral",
        }.get(tone, "StatusMuted")
        self._artwork_caption_label.setObjectName(object_name)
        self._artwork_caption_label.style().unpolish(self._artwork_caption_label)
        self._artwork_caption_label.style().polish(self._artwork_caption_label)

    def _prefetch_artwork_async(self) -> None:
        release = self.session.selected_release
        if release is None:
            return
        if self.session.album_artwork is not None and self.session.album_artwork.is_available:
            return
        if self._artwork_worker is not None and self._artwork_worker.isRunning():
            return

        fetcher = self._artwork_fetcher or fetch_release_artwork
        self._artwork_worker = _ArtworkFetchWorker(fetcher, release.id, self)
        self._artwork_worker.finished.connect(self._on_artwork_fetch_finished)
        self._artwork_worker.start()

    def _on_artwork_fetch_finished(self, result: object) -> None:
        self._artwork_worker = None
        if not isinstance(result, ArtworkFetchResult):
            return
        if result.artwork is not None and result.artwork.is_available:
            self.session.set_album_artwork(result.artwork)
            self._update_artwork_preview()
            self._set_artwork_caption(result.message, tone="success")
        else:
            self._set_artwork_caption(result.message, tone="muted")

    def _on_browse_clicked(self) -> None:
        current = self.session.output_directory
        if current is not None and current.is_dir():
            start_dir = str(current)
        else:
            settings = self.container.settings
            stored = settings.get(settings.KEY_LAST_EXPORT_DIR, "")
            if isinstance(stored, str) and stored and Path(stored).is_dir():
                start_dir = stored
            else:
                start_dir = str(Path.home())
        selected = QFileDialog.getExistingDirectory(
            self,
            "Choose Output Folder",
            start_dir,
        )
        if not selected:
            return
        output_directory = Path(selected)
        self.session.set_output_directory(output_directory)
        settings = self.container.settings
        settings.set(settings.KEY_LAST_EXPORT_DIR, str(output_directory))
        settings.sync()
        self._output_path_label.setText(str(output_directory))

    def _on_export_clicked(self) -> None:
        if self._export_worker is not None and self._export_worker.isRunning():
            return
        self._start_async_export()

    def _on_new_album_clicked(self) -> None:
        """Reset the session and restart the wizard at Open album."""
        wizard = self.wizard()
        if wizard is None:
            self.session.reset()
            return
        restart = getattr(wizard, "restart_for_new_album", None)
        if callable(restart):
            restart()
            return
        self.session.reset()
        wizard.restart()

    def _selected_export_format(self) -> ExportFormat | None:
        return resolve_export_format(self._format_combo.currentData())

    def _run_export(self, *, show_progress: bool) -> bool:
        """Validate settings, export every track, and update session state."""
        release = self.session.selected_release
        if release is None:
            self._set_status("No release is selected.", tone="error")
            return False

        output_directory = self.session.output_directory
        if output_directory is None:
            self._set_status("Choose an output folder before exporting.", tone="error")
            return False

        export_format = self._selected_export_format()
        if export_format is None:
            self._set_status("Choose a valid export format.", tone="error")
            return False

        self.session.set_export_format(export_format)
        if show_progress:
            self._set_export_loading(True, total=len(self.session.track_list))

        try:
            exporter = self._album_exporter or self._default_album_exporter
            result = exporter(
                self._on_export_progress if show_progress else None
            )
        finally:
            if show_progress:
                self._set_export_loading(False)

        self._apply_export_result(result)
        return (
            isinstance(result, AlbumExportResult)
            and result.success
            and self.session.export_completed
        )

    def _start_async_export(self) -> None:
        release = self.session.selected_release
        if release is None:
            self._set_status("No release is selected.", tone="error")
            return

        output_directory = self.session.output_directory
        if output_directory is None:
            self._set_status("Choose an output folder before exporting.", tone="error")
            return

        export_format = self._selected_export_format()
        if export_format is None:
            self._set_status("Choose a valid export format.", tone="error")
            return

        self.session.set_export_format(export_format)
        self._set_export_loading(True, total=len(self.session.track_list))
        exporter = self._album_exporter or self._default_album_exporter
        self._export_worker = _ExportWorker(exporter, self)
        self._export_worker.progress.connect(self._on_export_progress)
        self._export_worker.finished.connect(self._on_export_finished)
        self._export_worker.start()

    def _default_album_exporter(
        self,
        progress_callback: Callable[[int, int], None] | None,
    ) -> AlbumExportResult:
        client = self.audacity
        if not client.is_connected():
            client.connect()

        release = self.session.selected_release
        if release is None:
            return AlbumExportResult(success=False, message="No release is selected.")

        output_directory = self.session.output_directory
        export_format = self.session.export_format
        if output_directory is None or export_format is None:
            return AlbumExportResult(
                success=False,
                message="Export settings are incomplete.",
            )

        settings = ExportSettings(
            output_directory=output_directory,
            export_format=export_format,
        )
        return ExportEngine(client).export_album(
            release,
            settings=settings,
            artwork=self.session.album_artwork,
            progress_callback=progress_callback,
        )

    def _on_export_progress(self, current: int, total: int) -> None:
        if total > 0:
            self._progress_bar.setMaximum(total)
            self._progress_bar.setValue(current)
            self._set_status(f"Exporting track {current} of {total}…", tone="neutral")

    def _on_export_finished(self, result: object) -> None:
        self._set_export_loading(False)
        self._export_worker = None
        self._apply_export_result(result)

    def _apply_export_result(self, result: object) -> None:
        if not isinstance(result, AlbumExportResult):
            self._set_status("Export failed.", tone="error")
            return

        if not result.success:
            self.session.add_validation_error(result.message)
            self._set_status(result.message, tone="error")
            return

        self.session.clear_validation_errors()
        self.session.mark_export_completed(result.tracks_exported)
        self._set_status(result.message, tone="success")
        self._update_summary()
        self._update_wizard_finish_button()
        self.completeChanged.emit()
        _logger.info("Exported %d track(s)", result.tracks_exported)

    def apply_export_result(self, result: AlbumExportResult) -> None:
        """Apply an export result directly (used in tests)."""
        self._apply_export_result(result)

    def _set_status(self, text: str, *, tone: str = "muted") -> None:
        self._status_label.setText(text)
        object_name = {
            "success": "StatusSuccess",
            "error": "StatusError",
            "neutral": "StatusNeutral",
        }.get(tone, "StatusMuted")
        self._status_label.setObjectName(object_name)
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

    def _update_wizard_finish_button(self) -> None:
        wizard = self.wizard()
        if wizard is None:
            return
        finish_button = wizard.button(QWizard.WizardButton.FinishButton)
        finish_button.setText(
            finish_button_label(export_completed=self.session.export_completed)
        )

    def _set_export_loading(self, loading: bool, *, total: int = 0) -> None:
        self._progress_bar.setVisible(loading)
        self._export_button.setEnabled(not loading)
        self._browse_button.setEnabled(not loading)
        self._format_combo.setEnabled(not loading)
        if loading and total > 0:
            self._progress_bar.setRange(0, total)
            self._progress_bar.setValue(0)
        else:
            self._progress_bar.setValue(0)