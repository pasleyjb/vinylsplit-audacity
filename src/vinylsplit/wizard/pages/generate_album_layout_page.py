"""Generate Album Layout wizard page."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import ClassVar

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QWizardPage,
)

from vinylsplit.audacity.client import AudacityClient
from vinylsplit.core.container import Container
from vinylsplit.labels.audacity_regions import (
    RegionGenerationResult,
    create_regions_from_layout,
    fetch_audacity_regions,
)
from vinylsplit.labels.layout_engine import AlbumLayout, TrackRegion
from vinylsplit.labels.time_format import format_position, format_region_range
from vinylsplit.waveform.peaks import PeakOverview, load_peak_overview
from vinylsplit.waveform.widget import WaveformWidget
from vinylsplit.wizard.pages.base import WizardPageBase
from vinylsplit.wizard.pages.page_ids import PageId
from vinylsplit.wizard.ui_style import (
    configure_data_table,
    create_status_label,
    style_primary_button,
    style_secondary_button,
)

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
        self._progress_callback = callback

    def run(self) -> None:
        self.finished.emit(self._generator(self._progress_callback))


class _ExistingRegionsWorker(QThread):
    """Read existing Audacity labels without writing new ones."""

    finished = Signal(object)

    def __init__(
        self,
        fetcher: Callable[[], list[dict[str, object]]],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._fetcher = fetcher

    def run(self) -> None:
        try:
            self.finished.emit(self._fetcher())
        except Exception as exc:  # noqa: BLE001
            self.finished.emit(exc)


class _PeakLoadWorker(QThread):
    """Build waveform peaks off the UI thread."""

    finished = Signal(object)

    def __init__(self, path: Path, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._path = path

    def run(self) -> None:
        try:
            self.finished.emit(load_peak_overview(self._path))
        except Exception as exc:  # noqa: BLE001
            self.finished.emit(exc)


class GenerateAlbumLayoutPage(WizardPageBase):
    """Generate the complete album region layout in Audacity."""

    PAGE_ID: ClassVar[int] = PageId.ALIGN
    PAGE_TITLE: ClassVar[str] = "Align & hand off"
    PAGE_SUBTITLE: ClassVar[str] = (
        "Edit the lattice on the waveform, then write labels into Audacity."
    )
    # This page is dense; avoid a bottom stretch that piles controls onto the wave.
    _use_page_stretch: ClassVar[bool] = False

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
        existing_region_fetcher: Callable[[], list[dict[str, object]]] | None = None,
        peak_loader: Callable[[Path], PeakOverview] | None = None,
    ) -> None:
        self._audacity = audacity_client
        self._region_generator = region_generator
        self._existing_region_fetcher = existing_region_fetcher
        self._peak_loader = peak_loader
        self._worker: _RegionGenerationWorker | None = None
        self._skip_worker: _ExistingRegionsWorker | None = None
        self._peak_worker: _PeakLoadWorker | None = None
        self._loaded_peak_path: Path | None = None
        super().__init__(container, parent)

    def build_content(self) -> None:
        self._layout.addWidget(
            self._create_info_banner(
                "<b>Lattice editing:</b> drag track <b>1</b> to move <b>everything</b>. "
                "Drag track <b>N</b> to keep 1…N-1 fixed and move <b>N and later</b> "
                "(track N-1 stretches). Nudge buttons / ←→ move the whole lattice. "
                "<b>Wheel</b> zooms · <b>Alt-drag</b> pans. Then <b>Write Labels</b>."
            )
        )

        # Waveform card
        self._waveform = WaveformWidget()
        self._waveform.setMinimumHeight(200)
        self._waveform.setMaximumHeight(280)
        self._waveform.layout_changed.connect(self._on_layout_changed)
        self._waveform.layout_preview.connect(self._on_layout_preview)
        self._waveform.view_changed.connect(self._on_waveform_view_changed)
        self._layout.addWidget(self._waveform)

        # Toolbar under the wave (never overlaid)
        toolbar = QWidget()
        toolbar.setObjectName("WaveformToolbar")
        zoom_row = QHBoxLayout(toolbar)
        zoom_row.setContentsMargins(0, 4, 0, 4)
        zoom_row.setSpacing(8)

        self._zoom_in_btn = QPushButton()
        style_secondary_button(self._zoom_in_btn, "Zoom in")
        self._zoom_in_btn.clicked.connect(self._waveform.zoom_in)

        self._zoom_out_btn = QPushButton()
        style_secondary_button(self._zoom_out_btn, "Zoom out")
        self._zoom_out_btn.clicked.connect(self._waveform.zoom_out)

        self._zoom_fit_btn = QPushButton()
        style_secondary_button(self._zoom_fit_btn, "Fit all")
        self._zoom_fit_btn.clicked.connect(self._waveform.zoom_fit)

        self._zoom_markers_btn = QPushButton()
        style_secondary_button(self._zoom_markers_btn, "Frame markers")
        self._zoom_markers_btn.clicked.connect(self._waveform.zoom_to_markers)

        self._offset_label = QLabel("Offset: +0.00 s")
        self._offset_label.setObjectName("MutedLabel")

        self._zoom_label = create_status_label(tone="muted")

        # Lattice nudge — reliable even if mouse-drag is awkward on this platform.
        self._nudge_m10 = QPushButton()
        style_secondary_button(self._nudge_m10, "−10s")
        self._nudge_m10.clicked.connect(lambda: self._waveform.nudge_all(-10.0))
        self._nudge_m1 = QPushButton()
        style_secondary_button(self._nudge_m1, "−1s")
        self._nudge_m1.clicked.connect(lambda: self._waveform.nudge_all(-1.0))
        self._nudge_m01 = QPushButton()
        style_secondary_button(self._nudge_m01, "−0.1s")
        self._nudge_m01.clicked.connect(lambda: self._waveform.nudge_all(-0.1))
        self._nudge_p01 = QPushButton()
        style_secondary_button(self._nudge_p01, "+0.1s")
        self._nudge_p01.clicked.connect(lambda: self._waveform.nudge_all(0.1))
        self._nudge_p1 = QPushButton()
        style_secondary_button(self._nudge_p1, "+1s")
        self._nudge_p1.clicked.connect(lambda: self._waveform.nudge_all(1.0))
        self._nudge_p10 = QPushButton()
        style_secondary_button(self._nudge_p10, "+10s")
        self._nudge_p10.clicked.connect(lambda: self._waveform.nudge_all(10.0))

        zoom_row.addWidget(self._zoom_in_btn)
        zoom_row.addWidget(self._zoom_out_btn)
        zoom_row.addWidget(self._zoom_fit_btn)
        zoom_row.addWidget(self._zoom_markers_btn)
        zoom_row.addSpacing(10)
        zoom_row.addWidget(self._nudge_m10)
        zoom_row.addWidget(self._nudge_m1)
        zoom_row.addWidget(self._nudge_m01)
        zoom_row.addWidget(self._nudge_p01)
        zoom_row.addWidget(self._nudge_p1)
        zoom_row.addWidget(self._nudge_p10)
        zoom_row.addSpacing(10)
        zoom_row.addWidget(self._offset_label)
        zoom_row.addWidget(self._zoom_label, stretch=1)
        self._layout.addWidget(toolbar)

        # Compact track list
        self._preview_table = QTableWidget(0, len(_PREVIEW_COLUMNS))
        self._preview_table.setHorizontalHeaderLabels(_PREVIEW_COLUMNS)
        configure_data_table(self._preview_table, min_height=100)
        self._preview_table.setMaximumHeight(160)
        self._layout.addWidget(self._preview_table)

        # Actions
        buttons = QHBoxLayout()
        self._generate_button = QPushButton()
        style_primary_button(self._generate_button, "Hand off to Audacity")
        self._generate_button.clicked.connect(self._on_generate_clicked)
        buttons.addWidget(self._generate_button)

        self._skip_button = QPushButton()
        style_secondary_button(self._skip_button, "Skip — use existing labels")
        self._skip_button.setToolTip(
            "Do not create or overwrite labels. Use regions already in Audacity."
        )
        self._skip_button.clicked.connect(self._on_skip_clicked)
        buttons.addWidget(self._skip_button)
        buttons.addStretch()
        self._layout.addLayout(buttons)

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

    def isComplete(self) -> bool:
        return self.session.initial_regions_generated

    def initializePage(self) -> None:
        super().initializePage()
        self._populate_preview_table()
        self._refresh_waveform_markers()
        self._update_t1_label()
        self._ensure_waveform_loaded()
        if self.session.skipped_region_generation:
            self._status_label.setText(
                f"Using {self.session.regions_created_count} existing label(s) "
                "in Audacity (not overwritten)."
            )
        elif self.session.initial_regions_generated:
            self._status_label.setText(
                f"Wrote {self.session.regions_created_count} track region(s) in Audacity."
            )
        else:
            self._status_label.setText(
                "Drag T1 to move all · drag TN to move from N onward · then write labels."
            )
        self.completeChanged.emit()

    def _update_t1_label(self, layout: AlbumLayout | None = None) -> None:
        layout = layout if layout is not None else self.session.album_layout
        if layout is None or not layout.regions:
            self._offset_label.setText("T1 @ —")
            return
        t1 = layout.regions[0].start_seconds
        self._offset_label.setText(f"T1 @ {format_position(t1)} ({t1:+.2f}s)")

    def _on_layout_preview(self, layout: object) -> None:
        """Update table while dragging (widget already paints markers)."""
        if not isinstance(layout, AlbumLayout):
            return
        self._preview_table.setRowCount(len(layout.regions))
        for row_index, region in enumerate(layout.regions):
            self._set_preview_row(row_index, region)
        self._update_t1_label(layout)

    def _on_layout_changed(self, layout: object) -> None:
        """Commit an edited lattice into the session."""
        if not isinstance(layout, AlbumLayout):
            return
        self.session.set_edited_layout(layout)
        self._populate_preview_table()
        self._update_t1_label(layout)
        # Do not call set_layout again — widget already has the final lattice.
        self._status_label.setText(
            "Lattice updated. Write labels to apply in Audacity."
        )
        self.completeChanged.emit()

    def _refresh_waveform_markers(self) -> None:
        self._waveform.set_layout(self.session.album_layout)
        self._on_waveform_view_changed()

    def _on_waveform_view_changed(self) -> None:
        w = self._waveform
        self._zoom_label.setText(
            f"View {format_position(w.view_start)}–"
            f"{format_position(w.view_start + w.view_length)} "
            f"/ {format_position(w.full_duration)}"
        )

    def _ensure_waveform_loaded(self) -> None:
        path = self.session.source_audio_path
        if path is None:
            self._loaded_peak_path = None
            self._waveform.set_peaks(None)
            self._waveform.set_message(
                "Open a source audio file on Welcome for the waveform.\n"
                "You can still drag markers if a release is selected."
            )
            self._refresh_waveform_markers()
            return

        if self._loaded_peak_path == path and self._peak_worker is None:
            self._refresh_waveform_markers()
            return

        if self._peak_worker is not None and self._peak_worker.isRunning():
            return

        self._waveform.set_message(f"Loading waveform: {path.name}…")
        self._waveform.set_peaks(None)

        if self._peak_loader is not None:
            try:
                peaks = self._peak_loader(path)
            except Exception as exc:  # noqa: BLE001
                self._waveform.set_message(f"Could not load waveform: {exc}")
                return
            self._on_peaks_loaded(peaks)
            return

        self._peak_worker = _PeakLoadWorker(path, self)
        self._peak_worker.finished.connect(self._on_peaks_loaded)
        self._peak_worker.start()

    def _on_peaks_loaded(self, result: object) -> None:
        self._peak_worker = None
        if isinstance(result, Exception):
            self._waveform.set_message(f"Could not load waveform: {result}")
            self._refresh_waveform_markers()
            return
        if not isinstance(result, PeakOverview):
            self._waveform.set_message("Could not load waveform.")
            return

        self._loaded_peak_path = result.path
        if result.is_empty:
            self._waveform.set_peaks(None)
            self._waveform.set_message(
                "Waveform unavailable (install ffmpeg for FLAC/MP3, or use WAV)."
            )
        else:
            self._waveform.set_peaks(result)
            self._waveform.set_message("")
        self._refresh_waveform_markers()

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

    def _on_skip_clicked(self) -> None:
        if self._skip_worker is not None and self._skip_worker.isRunning():
            return

        self._set_loading(True, total=0, indeterminate=True)
        self._status_label.setText("Reading existing labels from Audacity…")

        fetcher = self._existing_region_fetcher or self._default_existing_fetcher
        self._skip_worker = _ExistingRegionsWorker(fetcher, self)
        self._skip_worker.finished.connect(self._on_skip_finished)
        self._skip_worker.start()

    def _default_existing_fetcher(self) -> list[dict[str, object]]:
        client = self.audacity
        if not client.is_connected():
            client.connect()
        return fetch_audacity_regions(client)

    def _on_skip_finished(self, result: object) -> None:
        self._set_loading(False)
        self._skip_worker = None

        if isinstance(result, Exception):
            self.session.add_validation_error(str(result))
            self._status_label.setText(str(result))
            self.completeChanged.emit()
            return

        if not isinstance(result, list):
            self._status_label.setText("Could not read labels from Audacity.")
            self.completeChanged.emit()
            return

        if not result:
            self._status_label.setText(
                "No labels found in Audacity. Write labels first, or create "
                "them in Audacity, then skip again."
            )
            self.completeChanged.emit()
            return

        count = len(result)
        self.session.clear_validation_errors()
        self.session.mark_using_existing_regions(count)
        self._status_label.setText(
            f"Using {count} existing label(s) in Audacity — nothing was "
            "overwritten. Continue to review or export with artwork."
        )
        self.completeChanged.emit()
        _logger.info("Skipped region generation; using %d existing label(s)", count)

    def apply_skip_regions(self, regions: list[dict[str, object]]) -> None:
        self._on_skip_finished(regions)

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
        self.session.skipped_region_generation = False
        self.session.mark_initial_regions_generated(result.regions_created)
        self._status_label.setText(result.message)
        self.completeChanged.emit()
        _logger.info("Generated %d track region(s) in Audacity", result.regions_created)

    def apply_region_generation_result(self, result: RegionGenerationResult) -> None:
        self._on_generation_finished(result)

    def _set_loading(
        self,
        loading: bool,
        *,
        total: int = 0,
        indeterminate: bool = False,
    ) -> None:
        self._progress_bar.setVisible(loading)
        self._generate_button.setEnabled(not loading)
        self._skip_button.setEnabled(not loading)
        self._waveform.setEnabled(not loading)
        for btn in (
            self._zoom_in_btn,
            self._zoom_out_btn,
            self._zoom_fit_btn,
            self._zoom_markers_btn,
            self._nudge_m10,
            self._nudge_m1,
            self._nudge_m01,
            self._nudge_p01,
            self._nudge_p1,
            self._nudge_p10,
        ):
            btn.setEnabled(not loading)
        if loading:
            if indeterminate or total <= 0:
                self._progress_bar.setRange(0, 0)
            else:
                self._progress_bar.setRange(0, total)
                self._progress_bar.setValue(0)
        else:
            self._progress_bar.setRange(0, 100)
            self._progress_bar.setValue(0)
