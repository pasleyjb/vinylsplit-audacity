"""Artist and album search wizard page."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import ClassVar

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWizardPage,
)

from vinylsplit.core.container import Container
from vinylsplit.metadata.models import Release, ReleaseSummary

from vinylsplit.musicbrainz.client import MusicBrainzClient
from vinylsplit.musicbrainz.exceptions import MusicBrainzError
from vinylsplit.wizard.pages.base import WizardPageBase
from vinylsplit.wizard.pages.page_ids import PageId
from vinylsplit.wizard.ui_style import (
    configure_data_table,
    create_status_label,
    style_primary_button,
)

_logger = logging.getLogger(__name__)

_TABLE_COLUMNS = [
    "Artist",
    "Album",
    "Release Year",
    "Country",
    "Track Count",
    "Release Type",
]


@dataclass(frozen=True)
class AlbumSearchResult:
    """Outcome of a background album search."""

    summaries: tuple[ReleaseSummary, ...] = ()
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None


@dataclass(frozen=True)
class ReleaseFetchResult:
    """Outcome of a background release lookup."""

    release: Release | None = None
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None and self.release is not None


class _AlbumSearchWorker(QThread):
    """Execute a MusicBrainz release search off the UI thread."""

    finished = Signal(object)

    def __init__(
        self,
        searcher: Callable[[str, str], list[ReleaseSummary]],
        artist: str,
        album: str,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._searcher = searcher
        self._artist = artist
        self._album = album

    def run(self) -> None:
        try:
            summaries = self._searcher(self._artist, self._album)
            self.finished.emit(AlbumSearchResult(summaries=tuple(summaries)))
        except MusicBrainzError as exc:
            self.finished.emit(AlbumSearchResult(error=str(exc)))
        except ValueError as exc:
            self.finished.emit(AlbumSearchResult(error=str(exc)))


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


class ArtistSearchPage(WizardPageBase):
    """Collect artist and album search terms and query MusicBrainz."""

    PAGE_ID: ClassVar[int] = PageId.ARTIST_SEARCH
    PAGE_TITLE: ClassVar[str] = "Artist & Album Search"
    PAGE_SUBTITLE: ClassVar[str] = "Enter the artist and album you are digitizing."

    def __init__(
        self,
        container: Container,
        parent: QWizardPage | None = None,
        *,
        musicbrainz_client: MusicBrainzClient | None = None,
    ) -> None:
        self._musicbrainz = musicbrainz_client
        self._search_worker: _AlbumSearchWorker | None = None
        self._fetch_worker: _ReleaseFetchWorker | None = None
        self._summaries: list[ReleaseSummary] = []
        self._loading_release_id: str | None = None
        super().__init__(container, parent)

    def build_content(self) -> None:
        self._layout.addWidget(
            self._create_info_banner(
                "<b>Search MusicBrainz</b><br>"
                "Enter the artist and album you are digitizing, then select the "
                "release that matches your vinyl pressing."
            )
        )

        form = QFormLayout()
        self.artist_input = QLineEdit()
        self.artist_input.setPlaceholderText("e.g. Pink Floyd")
        self.album_input = QLineEdit()
        self.album_input.setPlaceholderText("e.g. The Dark Side of the Moon")

        form.addRow("Artist:", self.artist_input)
        form.addRow("Album:", self.album_input)
        self._layout.addLayout(form)

        controls = QHBoxLayout()
        self._search_button = QPushButton()
        style_primary_button(self._search_button, "Search")
        self._search_button.clicked.connect(self._on_search_clicked)
        controls.addWidget(self._search_button)
        controls.addStretch()
        self._layout.addLayout(controls)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setVisible(False)
        self._layout.addWidget(self._progress_bar)

        self._status_label = create_status_label()
        self._layout.addWidget(self._status_label)

        self._results_table = QTableWidget(0, len(_TABLE_COLUMNS))
        self._results_table.setHorizontalHeaderLabels(_TABLE_COLUMNS)
        configure_data_table(self._results_table)
        self._results_table.itemSelectionChanged.connect(self._on_selection_changed)
        self._layout.addWidget(self._results_table)

    @property
    def musicbrainz(self) -> MusicBrainzClient:
        """MusicBrainz API client."""
        if self._musicbrainz is None:
            self._musicbrainz = self.container.resolve("musicbrainz")
        return self._musicbrainz

    def isComplete(self) -> bool:
        """Require a selected release before advancing."""
        return self.session.selected_release is not None

    def initializePage(self) -> None:
        super().initializePage()
        self._restore_search_fields()
        self.completeChanged.emit()

    def _restore_search_fields(self) -> None:
        """Restore in-session search terms when navigating back within the wizard."""
        if not self.artist_input.text() and self.session.last_artist_query:
            self.artist_input.setText(self.session.last_artist_query)
        if not self.album_input.text() and self.session.last_album_query:
            self.album_input.setText(self.session.last_album_query)

    def _on_search_clicked(self) -> None:
        if self._search_worker is not None and self._search_worker.isRunning():
            return

        artist = self.artist_input.text().strip()
        album = self.album_input.text().strip()
        if not artist and not album:
            self._status_label.setText("Enter an artist or album name to search.")
            return

        self._set_search_loading(True)
        self._status_label.setText("Searching MusicBrainz...")
        self.session.clear_selected_release()
        self.completeChanged.emit()

        self._search_worker = _AlbumSearchWorker(
            self.musicbrainz.search_releases,
            artist,
            album,
            self,
        )
        self._search_worker.finished.connect(self._on_search_finished)
        self._search_worker.start()

    def _on_search_finished(self, result: AlbumSearchResult) -> None:
        self._set_search_loading(False)
        self._search_worker = None

        if not result.success:
            self._summaries = []
            self._populate_results_table()
            error = result.error or "Search failed."
            self.session.add_validation_error(error)
            self._status_label.setText(error)
            return

        self.session.clear_validation_errors()

        self._summaries = list(result.summaries)
        self.session.search_results = list(result.summaries)
        self.session.last_artist_query = self.artist_input.text().strip()
        self.session.last_album_query = self.album_input.text().strip()
        self._populate_results_table()

        if not self._summaries:
            self._status_label.setText(
                "No releases found. Try different artist or album terms."
            )
            return

        count = len(self._summaries)
        noun = "release" if count == 1 else "releases"
        self._status_label.setText(
            f"Found {count} {noun}. Select the release that matches your vinyl."
        )

    def _populate_results_table(self) -> None:
        self._results_table.setRowCount(len(self._summaries))
        for row, summary in enumerate(self._summaries):
            values = [
                summary.artist,
                summary.album,
                summary.release_year,
                summary.country,
                str(summary.track_count),
                summary.release_type,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, summary.id)
                self._results_table.setItem(row, column, item)

        self._results_table.clearSelection()

    def _on_selection_changed(self) -> None:
        if self._fetch_worker is not None and self._fetch_worker.isRunning():
            return

        row = self._results_table.currentRow()
        if row < 0 or row >= len(self._summaries):
            return

        summary = self._summaries[row]
        selected = self.session.selected_release
        if selected is not None and selected.id == summary.id:
            return

        self._loading_release_id = summary.id
        self._set_fetch_loading(True, summary=summary)
        self._fetch_worker = _ReleaseFetchWorker(
            self.musicbrainz.get_release,
            summary.id,
            self,
        )
        self._fetch_worker.finished.connect(self._on_release_fetch_finished)
        self._fetch_worker.start()

    def _on_release_fetch_finished(self, result: ReleaseFetchResult) -> None:
        self._set_fetch_loading(False)
        self._fetch_worker = None
        self._loading_release_id = None

        if not result.success or result.release is None:
            self.session.clear_selected_release()
            self.completeChanged.emit()
            self._status_label.setText(
                result.error or "Could not load the selected release."
            )
            return

        self.session.set_selected_release(result.release)
        self.completeChanged.emit()
        self._status_label.setText(
            f"Selected: {result.release.artist_name} — {result.release.title} "
            f"({result.release.release_year})"
        )
        _logger.info("Stored release selection: %s", result.release.id)

    def apply_search_result(self, result: AlbumSearchResult) -> None:
        """Apply a search result directly (used in tests)."""
        self._on_search_finished(result)

    def apply_release_fetch_result(self, result: ReleaseFetchResult) -> None:
        """Apply a release fetch result directly (used in tests)."""
        self._on_release_fetch_finished(result)

    def _set_search_loading(self, loading: bool) -> None:
        self._progress_bar.setVisible(loading)
        self._search_button.setEnabled(not loading)
        self.artist_input.setEnabled(not loading)
        self.album_input.setEnabled(not loading)
        self._results_table.setEnabled(not loading)

    def _set_fetch_loading(
        self,
        loading: bool,
        *,
        summary: ReleaseSummary | None = None,
    ) -> None:
        self._progress_bar.setVisible(loading)
        self._search_button.setEnabled(not loading)
        if loading and summary is not None:
            self._status_label.setText(
                f"Loading release details for {summary.artist} — {summary.album}..."
            )
        self._results_table.setEnabled(not loading)
