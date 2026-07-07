"""Label placement wizard page."""

from __future__ import annotations

from typing import ClassVar

from vinylsplit.wizard.pages.base import WizardPageBase
from vinylsplit.wizard.pages.page_ids import PageId


class LabelPlacementPage(WizardPageBase):
    """Guide the user through placing Audacity labels at track boundaries."""

    PAGE_ID: ClassVar[int] = PageId.LABEL_PLACEMENT
    PAGE_TITLE: ClassVar[str] = "Label Placement"
    PAGE_SUBTITLE: ClassVar[str] = "Mark track boundaries in your Audacity project."

    def build_content(self) -> None:
        self._layout.addWidget(
            self._create_placeholder_label(
                "<b>Label Placement</b><br><br>"
                "In a future version, this page will:<br>"
                "<ul>"
                "<li>Connect to your open Audacity project</li>"
                "<li>Display waveform guidance for each track boundary</li>"
                "<li>Insert labels at the correct positions automatically "
                "or with your confirmation</li>"
                "</ul>"
                "Ensure Audacity is open with your vinyl recording loaded "
                "before proceeding."
            )
        )
