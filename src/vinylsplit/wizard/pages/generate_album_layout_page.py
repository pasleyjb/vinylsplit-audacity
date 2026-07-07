"""Generate Album Layout wizard page."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import ClassVar

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWizardPage,
)

from vinylsplit.audacity.client import AudacityClient
from vinylsplit.core.container import Container
from vinylsplit.labels.audacity_regions import (
    RegionGenerationResult,
    create_regions_from_layout,
)
from vinylsplit.labels.layout_engine import TrackRegion
from vinylsplit.labels.time_format import format_region_range
from vinylsplit.wizard.pages.base import WizardPageBase
from vinylsplit.wizard.pages.page_ids import PageId

_logger = logging.getLogger(__name__)

_PREVIEW_COLUMNS = ["#", "Title", "Region"]


class _RegionGenerationWorker(QThread):
    """Create Audacity regions off the UI thread."""

    finished = Signal(object)

    def __init__(
        self,
        generator: Callable[[Callable[[int, int], None] | None], RegionGenerationResult],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._generator = generator
        self._progress_callback: Callable[[int, int], None] | None = None

    def set_progress_callback(
        self,
        callback: Callable[[int, int], None],
    ) -> None:
        """Store a callback invoked as each region is created."""
        self._progress_callback = callback

    def run(self) -> None:
        self.finished.emit(self._generator(self._progress_callback))


class GenerateAlbumLayoutPage(WizardPageBase):
    """Generate the complete album region layout in Audacity."""

    PAGE_ID: ClassVar[int] = PageId.GENERATE_ALBUM_LAYOUT
    PAGE_TITLE: ClassVar[str] = "Generate Album Layout"
    PAGE_SUBTITLE: ClassVar[str] = (
        "Create every track region from MusicBrainz durations."
    )

    def __init__(
        self,
        container: Container,
        parent: QWizardPage | None = None,
        *,
        audacity_client: AudacityClient | None = None,
        region_generator: Callable[
            [Callable[[int, int], None] | None], RegionGenerationResult
        ]
        | None = None,
    ) -> None:
        self._audacity = audacity_client
        self._region_generator = region_generator
        self._worker: _RegionGenerationWorker | None = None
        super().__init__(container, parent)

    def build_content(self) -> None:
        self._layout.addWidget(
            self._create_placeholder_label(
                "<b>Generate Initial Regions</b><br>"
                "VinylSplit will create a complete album layout in Audacity "
                "using cumulative track durations from MusicBrainz."
            )
        )

        self._preview_table = QTableWidget(0, len(_PREVIEW_COLUMNS))
        self._preview_table.setHorizontalHeaderLabels(_PREVIEW_COLUMNS)
        self._preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._preview_table.verticalHeader().setVisible(False)
        header = self._preview_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._layout.addWidget(self._preview_table)

        self._generate_button = QPushButton("Generate Initial Regions")
        self._generate_button.clicked.connect(self._on_generate_clicked)
        self._layout.addWidget(self._generate_button)

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
        """Audacity pipe client."""
        if self._audacity is None:
            self._audacity = self.container.resolve("audacity")
        return self._audacity

    def isComplete(self) -> bool:
        """Require successful region generation before continuing."""
        return self.session.initial_regions_generated

    def initializePage(self) -> None:
        super().initializePage()
        self._populate_preview_table()
        if self.session.initial_regions_generated:
            self._status_label.setText(
                f"Created {self.session.regions_created_count} track region(s) in Audacity."
            )
        else:
            self._status_label.setText(
                "Press Generate Initial Regions to create the album layout in Audacity."
            )
        self.completeChanged.emit()

    def _populate_preview_table(self) -> None:
        layout = self.session.album_layout
        if layout is None:
            self._preview_table.setRowCount(0)
            return

        self._preview_table.setRowCount(len(layout.regions))
        for row_index, region in enumerate(layout.regions):
            self._set_preview_row(row_index, region)

    def _set_preview_row(self, row_index: int, region: TrackRegion) -> None:
        values = [
            region.track_number,
            region.title,
            format_region_range(region.start_seconds, region.end_seconds),
        ]
        for column, value in enumerate(values):
            self._preview_table.setItem(row_index, column, QTableWidgetItem(value))

    def _on_generate_clicked(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return

        layout = self.session.album_layout
        if layout is None or not layout.regions:
            self._status_label.setText("No album layout is available.")
            return

        self.session.start_layout_generation()
        self._set_loading(True, total=len(layout.regions))

        generator = self._region_generator or self._default_region_generator
        self._worker = _RegionGenerationWorker(generator, self)
        self._worker.set_progress_callback(self._on_generation_progress)
        self._worker.finished.connect(self._on_generation_finished)
        self._worker.start()

    def _default_region_generator(
        self,
        progress_callback: Callable[[int, int], None] | None,
    ) -> RegionGenerationResult:
        client = self.audacity
        if not client.is_connected():
            client.connect()
        layout = self.session.album_layout
        if layout is None:
            return RegionGenerationResult(
                success=False,
                message="No album layout is available.",
            )
        return create_regions_from_layout(
            client,
            layout,
            progress_callback=progress_callback,
        )

    def _on_generation_progress(self, current: int, total: int) -> None:
        if total > 0:
            self._progress_bar.setMaximum(total)
            self._progress_bar.setValue(current)
            self._status_label.setText(f"Creating region {current} of {total}…")

    def _on_generation_finished(self, result: object) -> None:
        self._set_loading(False)
        self._worker = None

        if not isinstance(result, RegionGenerationResult):
            self._status_label.setText("Could not generate track regions.")
            return

        if not result.success:
            self.session.add_validation_error(result.message)
            self._status_label.setText(result.message)
            self.completeChanged.emit()
            return

        self.session.clear_validation_errors()
        self.session.mark_initial_regions_generated(result.regions_created)
        self._status_label.setText(result.message)
        self.completeChanged.emit()
        _logger.info("Generated %d track region(s) in Audacity", result.regions_created)

    def apply_region_generation_result(self, result: RegionGenerationResult) -> None:
        """Apply a generation result directly (used in tests)."""
        self._on_generation_finished(result)

    def _set_loading(self, loading: bool, *, total: int = 0) -> None:
        self._progress_bar.setVisible(loading)
        self._generate_button.setEnabled(not loading)
        if loading and total > 0:
            self._progress_bar.setRange(0, total)
            self._progress_bar.setValue(0)
        else:
            self._progress_bar.setValue(0)