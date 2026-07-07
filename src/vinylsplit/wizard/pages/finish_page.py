"""Finish wizard page."""

from __future__ import annotations

from typing import ClassVar

from vinylsplit.wizard.pages.base import WizardPageBase
from vinylsplit.wizard.pages.page_ids import PageId


class FinishPage(WizardPageBase):
    """Final confirmation and next-step guidance."""

    PAGE_ID: ClassVar[int] = PageId.FINISH
    PAGE_TITLE: ClassVar[str] = "Finish"
    PAGE_SUBTITLE: ClassVar[str] = "You are ready to export your tracks."

    def build_content(self) -> None:
        self._layout.addWidget(
            self._create_placeholder_label(
                "<b>All Done!</b><br><br>"
                "Export automation is not yet available in version 0.1. "
                "When implemented, clicking <b>Finish</b> will apply your "
                "labels in Audacity and optionally export each track as a "
                "separate file.<br><br>"
                "Thank you for trying VinylSplit for Audacity."
            )
        )
