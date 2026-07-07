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

    PAGE_ID: ClassVar[int] = PageId.FINISH
    PAGE_TITLE: ClassVar[str] = "Finish"
    PAGE_SUBTITLE: ClassVar[str] = "Export your tracks with metadata and artwork."

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
        self._summary_label = self._create_placeholder_label("")
        self._layout.addWidget(self._summary_label)

        form = QFormLayout()
        self._format_combo = QComboBox()
        for export_format in ExportFormat:
            self._format_combo.addItem(export_format.value.upper(), export_format)
        form.addRow("Format:", self._format_combo)

        self._output_path_label = QLabel("Not selected")
        self._output_path_label.setWordWrap(True)
        self._browse_button = QPushButton("Choose Folder…")
        self._browse_button.clicked.connect(self._on_browse_clicked)
        output_row = QWidget()
        output_layout = QHBoxLayout(output_row)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.addWidget(self._output_path_label, stretch=1)
        output_layout.addWidget(self._browse_button)
        form.addRow("Output folder:", output_row)

        self._layout.addLayout(form)

        self._artwork_label = QLabel("")
        self._artwork_label.setWordWrap(True)
        self._layout.addWidget(self._artwork_label)

        self._export_button = QPushButton("Export Tracks")
        self._export_button.clicked.connect(self._on_export_clicked)
        self._layout.addWidget(self._export_button)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        self._layout.addWidget(self._progress_bar)

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)
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
        self._update_artwork_status()
        if self._prefetch_artwork:
            self._prefetch_artwork_async()
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

        self._summary_label.setText(
            "<b>Album Layout Complete</b><br><br>"
            f"<b>Artist:</b> {release.artist_name}<br>"
            f"<b>Album:</b> {release.title}<br>"
            f"<b>Regions created:</b> {regions_created}<br>"
            f"<b>Layout generation time:</b> {elapsed_text}<br><br>"
            f"{export_note}"
        )

    def _update_artwork_status(self) -> None:
        artwork = self.session.album_artwork
        if artwork is not None and artwork.is_available:
            self._artwork_label.setText("Album artwork is ready for embedding.")
            return
        self._artwork_label.setText(
            "Album artwork will be downloaded from Cover Art Archive during export."
        )

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
            self._artwork_label.setText(result.message)
        else:
            self._artwork_label.setText(result.message)

    def _on_browse_clicked(self) -> None:
        current = self.session.output_directory
        start_dir = str(current) if current is not None else str(Path.home())
        selected = QFileDialog.getExistingDirectory(
            self,
            "Choose Output Folder",
            start_dir,
        )
        if not selected:
            return
        output_directory = Path(selected)
        self.session.set_output_directory(output_directory)
        self._output_path_label.setText(str(output_directory))

    def _on_export_clicked(self) -> None:
        if self._export_worker is not None and self._export_worker.isRunning():
            return
        self._start_async_export()

    def _selected_export_format(self) -> ExportFormat | None:
        return resolve_export_format(self._format_combo.currentData())

    def _run_export(self, *, show_progress: bool) -> bool:
        """Validate settings, export every track, and update session state."""
        release = self.session.selected_release
        if release is None:
            self._status_label.setText("No release is selected.")
            return False

        output_directory = self.session.output_directory
        if output_directory is None:
            self._status_label.setText("Choose an output folder before exporting.")
            return False

        export_format = self._selected_export_format()
        if export_format is None:
            self._status_label.setText("Choose a valid export format.")
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
            self._status_label.setText("No release is selected.")
            return

        output_directory = self.session.output_directory
        if output_directory is None:
            self._status_label.setText("Choose an output folder before exporting.")
            return

        export_format = self._selected_export_format()
        if export_format is None:
            self._status_label.setText("Choose a valid export format.")
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
            self._status_label.setText(f"Exporting track {current} of {total}…")

    def _on_export_finished(self, result: object) -> None:
        self._set_export_loading(False)
        self._export_worker = None
        self._apply_export_result(result)

    def _apply_export_result(self, result: object) -> None:
        if not isinstance(result, AlbumExportResult):
            self._status_label.setText("Export failed.")
            return

        if not result.success:
            self.session.add_validation_error(result.message)
            self._status_label.setText(result.message)
            return

        self.session.clear_validation_errors()
        self.session.mark_export_completed(result.tracks_exported)
        self._status_label.setText(result.message)
        self._update_summary()
        self.completeChanged.emit()
        _logger.info("Exported %d track(s)", result.tracks_exported)

    def apply_export_result(self, result: AlbumExportResult) -> None:
        """Apply an export result directly (used in tests)."""
        self._apply_export_result(result)

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