"""Release selection wizard page."""

from __future__ import annotations

from typing import ClassVar

from PySide6.QtWidgets import QListWidget

from vinylsplit.wizard.pages.base import WizardPageBase
from vinylsplit.wizard.pages.page_ids import PageId


class ReleaseSelectionPage(WizardPageBase):
    """Display candidate releases returned from MusicBrainz."""

    PAGE_ID: ClassVar[int] = PageId.RELEASE_SELECTION
    PAGE_TITLE: ClassVar[str] = "Release Selection"
    PAGE_SUBTITLE: ClassVar[str] = (
        "Choose the release that matches your vinyl pressing."
    )

    def build_content(self) -> None:
        self.release_list = QListWidget()
        self.release_list.addItems(
            [
                "(Placeholder) 1973 UK vinyl — EMI",
                "(Placeholder) 1973 US vinyl — Harvest",
                "(Placeholder) 2011 remaster — EMI",
            ]
        )
        self._layout.addWidget(self.release_list)

        self._layout.addWidget(
            self._create_placeholder_label(
                "Release data will be loaded from MusicBrainz in a future version."
            )
        )
