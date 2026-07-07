"""Review wizard page."""

from __future__ import annotations

from typing import ClassVar

from vinylsplit.wizard.pages.base import WizardPageBase
from vinylsplit.wizard.pages.page_ids import PageId


class ReviewPage(WizardPageBase):
    """Summarize choices before applying labels and exporting."""

    PAGE_ID: ClassVar[int] = PageId.REVIEW
    PAGE_TITLE: ClassVar[str] = "Review"
    PAGE_SUBTITLE: ClassVar[str] = "Confirm your selections before finishing."

    def build_content(self) -> None:
        self._layout.addWidget(
            self._create_placeholder_label(
                "<b>Review Summary</b><br><br>"
                "A summary of your artist, album, release, tracks, and label "
                "positions will appear here once the workflow is fully "
                "implemented."
            )
        )

    def initializePage(self) -> None:
        super().initializePage()
        # Future: populate summary from shared wizard state / metadata store.
