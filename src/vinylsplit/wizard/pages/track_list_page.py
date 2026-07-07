"""Track list wizard page."""

from __future__ import annotations

from typing import ClassVar

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

from vinylsplit.wizard.pages.base import WizardPageBase
from vinylsplit.wizard.pages.page_ids import PageId


class TrackListPage(WizardPageBase):
    """Show the track listing for the selected release."""

    PAGE_ID: ClassVar[int] = PageId.TRACK_LIST
    PAGE_TITLE: ClassVar[str] = "Track List"
    PAGE_SUBTITLE: ClassVar[str] = "Review the tracks that will be created in Audacity."

    def build_content(self) -> None:
        self.track_table = QTableWidget(5, 3)
        self.track_table.setHorizontalHeaderLabels(["#", "Title", "Duration"])
        self.track_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        placeholder_tracks = [
            ("1", "Speak to Me", "1:30"),
            ("2", "Breathe", "2:43"),
            ("3", "On the Run", "3:36"),
            ("4", "Time", "6:53"),
            ("5", "The Great Gig in the Sky", "4:36"),
        ]
        for row, (number, title, duration) in enumerate(placeholder_tracks):
            self.track_table.setItem(row, 0, QTableWidgetItem(number))
            self.track_table.setItem(row, 1, QTableWidgetItem(title))
            self.track_table.setItem(row, 2, QTableWidgetItem(duration))

        self.track_table.resizeColumnsToContents()
        self._layout.addWidget(self.track_table)

        self._layout.addWidget(
            self._create_placeholder_label(
                "Track metadata will be populated from the selected MusicBrainz release."
            )
        )
