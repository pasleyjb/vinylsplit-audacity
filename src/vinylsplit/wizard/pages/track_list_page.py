"""Track list wizard page."""

from __future__ import annotations

from typing import ClassVar

from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem

from vinylsplit.metadata.tracks import format_numbered_track_line, format_track_length
from vinylsplit.wizard.pages.base import WizardPageBase
from vinylsplit.wizard.pages.page_ids import PageId

_TABLE_COLUMNS = ["#", "Title", "Duration"]


class TrackListPage(WizardPageBase):
    """Review the official track listing before generating the album layout."""

    PAGE_ID: ClassVar[int] = PageId.TRACK_LIST
    PAGE_TITLE: ClassVar[str] = "Track List"
    PAGE_SUBTITLE: ClassVar[str] = (
        "Review the tracks from the selected MusicBrainz release."
    )

    def build_content(self) -> None:
        self._layout.addWidget(
            self._create_placeholder_label(
                "<b>Review Track List</b><br>"
                "Confirm the official track listing before generating the "
                "initial album layout in Audacity."
            )
        )

        self.track_table = QTableWidget(0, len(_TABLE_COLUMNS))
        self.track_table.setHorizontalHeaderLabels(_TABLE_COLUMNS)
        self.track_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.track_table.verticalHeader().setVisible(False)
        header = self.track_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._layout.addWidget(self.track_table)

    def isComplete(self) -> bool:
        """Require a release with an official track listing."""
        return bool(self.session.track_list)

    def initializePage(self) -> None:
        super().initializePage()
        self._populate_track_table()
        self.completeChanged.emit()

    def _populate_track_table(self) -> None:
        tracks = self.session.track_list
        self.track_table.setRowCount(len(tracks))

        for row, track in enumerate(tracks):
            values = [
                format_numbered_track_line(track).split(" ", 1)[0],
                track.title,
                format_track_length(track.length_ms),
            ]
            for column, value in enumerate(values):
                self.track_table.setItem(row, column, QTableWidgetItem(value))