"""Review Album Layout wizard page."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import ClassVar

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWizardPage,
)

from vinylsplit.audacity.client import AudacityClient, AudacityError
from vinylsplit.core.container import Container
from vinylsplit.labels.audacity_regions import fetch_audacity_regions
from vinylsplit.labels.region_review import RegionReviewRow, build_region_review_rows
from vinylsplit.wizard.pages.base import WizardPageBase
from vinylsplit.wizard.pages.page_ids import PageId
from vinylsplit.wizard.ui_style import (
    configure_data_table,
    create_status_label,
    style_primary_button,
)

_logger = logging.getLogger(__name__)

_REVIEW_COLUMNS = [
    "Track",
    "Title",
    "Expected",
    "Actual",
    "Difference",
    "Status",
]


class _RegionRefreshWorker(QThread):
    """Fetch Audacity regions off the UI thread."""

    finished = Signal(object)

    def __init__(
        self,
        fetcher: Callable[[], list[dict[str, object]]],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._fetcher = fetcher

    def run(self) -> None:
        self.finished.emit(self._fetcher())


class ReviewPage(WizardPageBase):
    """Review track region boundaries after the user adjusts them in Audacity."""

    PAGE_ID: ClassVar[int] = PageId.REVIEW
    PAGE_TITLE: ClassVar[str] = "Review Album Layout"
    PAGE_SUBTITLE: ClassVar[str] = (
        "Compare expected and current region boundaries before export."
    )

    def __init__(
        self,
        container: Container,
        parent: QWizardPage | None = None,
        *,
        audacity_client: AudacityClient | None = None,
        region_fetcher: Callable[[], list[dict[str, object]]] | None = None,
    ) -> None:
        self._audacity = audacity_client
        self._region_fetcher = region_fetcher
        self._worker: _RegionRefreshWorker | None = None
        super().__init__(container, parent)

    def build_content(self) -> None:
        self._layout.addWidget(
            self._create_info_banner(
                "<b>Review the generated track regions inside Audacity.</b><br><br>"
                "Drag any boundaries that require adjustment.<br>"
                "When finished click <b>Refresh</b>."
            )
        )

        self._review_table = QTableWidget(0, len(_REVIEW_COLUMNS))
        self._review_table.setHorizontalHeaderLabels(_REVIEW_COLUMNS)
        configure_data_table(self._review_table)
        self._layout.addWidget(self._review_table)

        self._refresh_button = QPushButton()
        style_primary_button(self._refresh_button, "Refresh")
        self._refresh_button.clicked.connect(self._on_refresh_clicked)
        self._layout.addWidget(self._refresh_button)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setVisible(False)
        self._layout.addWidget(self._progress_bar)

        self._status_label = create_status_label()
        self._layout.addWidget(self._status_label)

    @property
    def audacity(self) -> AudacityClient:
        """Audacity pipe client."""
        if self._audacity is None:
            self._audacity = self.container.resolve("audacity")
        return self._audacity

    def isComplete(self) -> bool:
        """Require a successful refresh before continuing to export."""
        return self.session.ready_for_export()

    def initializePage(self) -> None:
        super().initializePage()
        if self.session.skipped_region_generation and self.session.layout_review_refreshed:
            self._status_label.setText(
                "Using existing Audacity labels (generation was skipped). "
                "Optional: adjust in Audacity and press Refresh, or continue to export."
            )
            self._refresh_review_table_from_session()
        elif self.session.layout_review_refreshed:
            self._refresh_review_table_from_session()
        else:
            self._status_label.setText(
                "Adjust regions in Audacity, then press Refresh to load their boundaries."
            )
        self.completeChanged.emit()

    def _on_refresh_clicked(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return

        self._set_loading(True)
        fetcher = self._region_fetcher or self._default_region_fetcher
        self._worker = _RegionRefreshWorker(fetcher, self)
        self._worker.finished.connect(self._on_refresh_finished)
        self._worker.start()

    def _default_region_fetcher(self) -> list[dict[str, object]]:
        client = self.audacity
        if not client.is_connected():
            client.connect()
        return fetch_audacity_regions(client)

    def _on_refresh_finished(self, regions: object) -> None:
        self._set_loading(False)
        self._worker = None

        if isinstance(regions, Exception):
            self.session.add_validation_error(str(regions))
            self._status_label.setText(str(regions))
            return

        if not isinstance(regions, list):
            self._status_label.setText("Could not read regions from Audacity.")
            return

        layout = self.session.album_layout
        if layout is None:
            self._status_label.setText("No album layout is available.")
            return

        rows = build_region_review_rows(layout, regions)
        self._populate_review_table(rows)
        self.session.clear_validation_errors()
        self.session.mark_layout_review_refreshed()
        warning_count = sum(1 for row in rows if row.has_warning)
        if warning_count:
            self._status_label.setText(
                f"Loaded {len(rows)} region(s). {warning_count} boundary(ies) differ "
                "by more than 2 seconds."
            )
        else:
            self._status_label.setText(
                f"Loaded {len(rows)} region(s). All boundaries are within 2 seconds."
            )
        self.completeChanged.emit()
        _logger.info("Refreshed region review with %d row(s)", len(rows))

    def apply_refresh_regions(self, regions: list[dict[str, object]]) -> None:
        """Apply a region refresh directly (used in tests)."""
        self._on_refresh_finished(regions)

    def _refresh_review_table_from_session(self) -> None:
        fetcher = self._region_fetcher or self._default_region_fetcher
        try:
            regions = fetcher()
        except (AudacityError, OSError) as exc:
            self._status_label.setText(str(exc))
            return

        layout = self.session.album_layout
        if layout is None:
            return

        rows = build_region_review_rows(layout, regions)
        self._populate_review_table(rows)

    def _populate_review_table(self, rows: list[RegionReviewRow]) -> None:
        self._review_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            status = "⚠ Warning" if row.has_warning else "✓"
            values = [
                row.track_number,
                row.title,
                row.expected_display,
                row.actual_display,
                row.difference_display,
                status,
            ]
            for column, value in enumerate(values):
                self._review_table.setItem(row_index, column, QTableWidgetItem(value))

    def _set_loading(self, loading: bool) -> None:
        self._progress_bar.setVisible(loading)
        self._refresh_button.setEnabled(not loading)