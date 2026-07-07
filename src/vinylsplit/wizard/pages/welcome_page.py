"""Welcome wizard page."""

from __future__ import annotations

from typing import ClassVar

from vinylsplit.wizard.pages.base import WizardPageBase
from vinylsplit.wizard.pages.page_ids import PageId


class WelcomePage(WizardPageBase):
    """Introduce the application and outline the digitization workflow."""

    PAGE_ID: ClassVar[int] = PageId.WELCOME
    PAGE_TITLE: ClassVar[str] = "Welcome"
    PAGE_SUBTITLE: ClassVar[str] = (
        "Split your vinyl recording into tracks using MusicBrainz metadata."
    )

    def build_content(self) -> None:
        self._layout.addWidget(
            self._create_placeholder_label(
                "<b>Welcome to VinylSplit for Audacity</b><br><br>"
                "This wizard will guide you through:<br>"
                "<ol>"
                "<li>Searching for your album on MusicBrainz</li>"
                "<li>Selecting the correct release</li>"
                "<li>Reviewing the track listing</li>"
                "<li>Placing labels in Audacity</li>"
                "<li>Exporting individual tracks</li>"
                "</ol>"
                "Click <b>Next</b> to begin."
            )
        )
