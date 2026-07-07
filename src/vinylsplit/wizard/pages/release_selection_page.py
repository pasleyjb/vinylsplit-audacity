"""Release selection wizard page."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import ClassVar

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QWizardPage,
)

from vinylsplit.core.container import Container
from vinylsplit.metadata.models import Release, ReleaseSummary, Track

from vinylsplit.metadata.tracks import (
    flatten_tracks,
    format_numbered_track_list,
    format_track_length,
    format_track_number,
)
from vinylsplit.musicbrainz.client import MusicBrainzClient
from vinylsplit.musicbrainz.exceptions import MusicBrainzError
from vinylsplit.wizard.pages.base import WizardPageBase
from vinylsplit.wizard.pages.page_ids import PageId

_logger = logging.getLogger(__name__)

_TRACK_TABLE_COLUMNS = ["Track Number", "Title", "Length"]


@dataclass(frozen=True)
class ReleaseFetchResult:
    """Outcome of a background release lookup."""

    release: Release | None = None
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None and self.release is not None


class _ReleaseFetchWorker(QThread):
    """Fetch a complete release off the UI thread."""

    finished = Signal(object)

    def __init__(
        self,
        fetcher: Callable[[str], Release],
        release_id: str,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._fetcher = fetcher
        self._release_id = release_id

    def run(self) -> None:
        try:
            release = self._fetcher(self._release_id)
            self.finished.emit(ReleaseFetchResult(release=release))
        except MusicBrainzError as exc:
            self.finished.emit(ReleaseFetchResult(error=str(exc)))
        except ValueError as exc:
            self.finished.emit(ReleaseFetchResult(error=str(exc)))


class ReleaseSelectionPage(WizardPageBase):
    """Display candidate releases and review their official track listings."""

    PAGE_ID: ClassVar[int] = PageId.RELEASE_SELECTION
    PAGE_TITLE: ClassVar[str] = "Release Selection"
    PAGE_SUBTITLE: ClassVar[str] = (
        "Choose the release that matches your vinyl pressing."
    )

    def __init__(
        self,
        container: Container,
        parent: QWizardPage | None = None,
        *,
        musicbrainz_client: MusicBrainzClient | None = None,
    ) -> None:
        self._musicbrainz = musicbrainz_client
        self._fetch_worker: _ReleaseFetchWorker | None = None
        self._summaries: list[ReleaseSummary] = []
        super().__init__(container, parent)

    def build_content(self) -> None:
        self._layout.addWidget(
            self._create_placeholder_label("<b>Available Releases</b>")
        )

        self.release_list = QListWidget()
        self.release_list.currentItemChanged.connect(self._on_release_selected)
        self._layout.addWidget(self.release_list)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setVisible(False)
        self._layout.addWidget(self._progress_bar)

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)
        self._layout.addWidget(self._status_label)

        self._release_summary_label = QLabel("")
        self._release_summary_label.setWordWrap(True)
        self._layout.addWidget(self._release_summary_label)

        self._track_list_label = QLabel("")
        self._track_list_label.setWordWrap(True)
        mono_font = QFont("Monospace")
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        self._track_list_label.setFont(mono_font)
        self._layout.addWidget(self._track_list_label)

        self._track_table = QTableWidget(0, len(_TRACK_TABLE_COLUMNS))
        self._track_table.setHorizontalHeaderLabels(_TRACK_TABLE_COLUMNS)
        self._track_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._track_table.verticalHeader().setVisible(False)
        header = self._track_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._layout.addWidget(self._track_table)

    @property
    def musicbrainz(self) -> MusicBrainzClient:
        """MusicBrainz API client."""
        if self._musicbrainz is None:
            self._musicbrainz = self.container.resolve("musicbrainz")
        return self._musicbrainz

    def isComplete(self) -> bool:
        """Require a release with an official track listing."""
        return self.session.has_selected_release() and bool(self.session.track_list)

    def initializePage(self) -> None:
        super().initializePage()
        self._populate_release_list()
        selected = self.session.selected_release
        if selected is not None:
            self._select_release_by_id(selected.id)
            if flatten_tracks(selected):
                self._display_release(selected)
        self.completeChanged.emit()

    def _populate_release_list(self) -> None:
        self._summaries = list(self.session.search_results)
        self.release_list.clear()

        if not self._summaries:
            self._status_label.setText(
                "No releases to review. Go back and search MusicBrainz first."
            )
            return

        for summary in self._summaries:
            item = QListWidgetItem(_format_release_list_item(summary))
            item.setData(Qt.ItemDataRole.UserRole, summary.id)
            self.release_list.addItem(item)

    def _select_release_by_id(self, release_id: str) -> None:
        for row in range(self.release_list.count()):
            item = self.release_list.item(row)
            if item is not None and item.data(Qt.ItemDataRole.UserRole) == release_id:
                self.release_list.setCurrentItem(item)
                return

    def _on_release_selected(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        if current is None:
            return

        release_id = str(current.data(Qt.ItemDataRole.UserRole))
        existing = self.session.selected_release
        if (
            existing is not None
            and existing.id == release_id
            and flatten_tracks(existing)
        ):
            self._display_release(existing)
            self.completeChanged.emit()
            return

        if self._fetch_worker is not None and self._fetch_worker.isRunning():
            return

        self._set_loading(True, summary=_summary_for_id(self._summaries, release_id))
        self._fetch_worker = _ReleaseFetchWorker(
            self.musicbrainz.get_release,
            release_id,
            self,
        )
        self._fetch_worker.finished.connect(self._on_release_fetch_finished)
        self._fetch_worker.start()

    def _on_release_fetch_finished(self, result: ReleaseFetchResult) -> None:
        self._set_loading(False)
        self._fetch_worker = None

        if not result.success or result.release is None:
            self.session.clear_selected_release()
            self._clear_track_display()
            self.completeChanged.emit()
            error = result.error or "Could not download the official track listing."
            self.session.add_validation_error(error)
            self._status_label.setText(error)
            return

        self.session.clear_validation_errors()
        self.session.set_selected_release(result.release)
        self._display_release(result.release)
        self.completeChanged.emit()
        _logger.info(
            "Release selection stored: %s (%d tracks)",
            result.release.id,
            len(flatten_tracks(result.release)),
        )

    def apply_release_fetch_result(self, result: ReleaseFetchResult) -> None:
        """Apply a fetch result directly (used in tests)."""
        self._on_release_fetch_finished(result)

    def _display_release(self, release: Release) -> None:
        tracks = flatten_tracks(release)
        self._release_summary_label.setText(
            f"<b>{release.artist_name}</b> — {release.title} "
            f"({release.release_year}, {release.country or '—'})"
        )
        self._track_list_label.setText(format_numbered_track_list(release))
        self._populate_track_table(tracks)
        self._status_label.setText(
            f"Loaded {len(tracks)} official track(s) from MusicBrainz."
        )

    def _populate_track_table(self, tracks: list[Track]) -> None:
        self._track_table.setRowCount(len(tracks))
        for row, track in enumerate(tracks):
            values = [
                format_track_number(track),
                track.title,
                format_track_length(track.length_ms),
            ]
            for column, value in enumerate(values):
                self._track_table.setItem(row, column, QTableWidgetItem(value))

    def _clear_track_display(self) -> None:
        self._release_summary_label.clear()
        self._track_list_label.clear()
        self._track_table.setRowCount(0)

    def _set_loading(
        self, loading: bool, *, summary: ReleaseSummary | None = None
    ) -> None:
        self._progress_bar.setVisible(loading)
        self.release_list.setEnabled(not loading)
        self._track_table.setEnabled(not loading)
        if loading and summary is not None:
            self._status_label.setText(
                f"Downloading official track listing for {summary.artist} — "
                f"{summary.album}..."
            )


def _format_release_list_item(summary: ReleaseSummary) -> str:
    """Format a release summary for the selection list."""
    return (
        f"{summary.release_year} {summary.country} — {summary.album} "
        f"({summary.release_type}) — {summary.track_count} tracks"
    )


def _summary_for_id(
    summaries: list[ReleaseSummary],
    release_id: str,
) -> ReleaseSummary | None:
    for summary in summaries:
        if summary.id == release_id:
            return summary
    return None
