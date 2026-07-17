"""Main VinylSplit wizard."""

from __future__ import annotations

import logging

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWizard

from vinylsplit import __app_name__
from vinylsplit.core.container import Container
from vinylsplit.metadata.session import WizardSession
from vinylsplit.wizard.pages import (
    ArtistSearchPage,
    FinishPage,
    GenerateAlbumLayoutPage,
    WelcomePage,
)
from vinylsplit.wizard.pages.page_ids import PageId
from vinylsplit.wizard.ui_style import apply_wizard_theme, finish_button_label

_logger = logging.getLogger(__name__)


class VinylSplitWizard(QWizard):
    """Four-step wizard for the vinyl digitization workflow.

    1. Open album (file + Audacity)
    2. Find release (MusicBrainz)
    3. Align lattice & hand off to Audacity
    4. Final approval & export (or start a new album)
    """

    def __init__(self, container: Container, parent: QWizard | None = None) -> None:
        super().__init__(parent)
        self._container = container
        self._logger = logging.getLogger(__name__)

        self.setWindowTitle(__app_name__)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.HaveHelpButton, False)
        self.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)
        self.setOption(QWizard.WizardOption.NoCancelButton, False)
        self.setOption(QWizard.WizardOption.NoDefaultButton, False)
        self.setMinimumSize(960, 720)
        apply_wizard_theme(self)

        self._register_pages()
        self.setStartId(PageId.OPEN)
        self.currentIdChanged.connect(self._on_page_changed)

        self._logger.info(
            "Wizard initialized with streamlined flow: Open → Release → Align → Export"
        )

    @property
    def container(self) -> Container:
        """Dependency injection container shared by all pages."""
        return self._container

    @property
    def session(self) -> WizardSession:
        """Wizard session state for the active workflow."""
        return self._container.session

    def restart_for_new_album(self) -> None:
        """Clear session state and return to the Open page."""
        self.session.reset()
        self.restart()
        self._logger.info("Restarted wizard for a new album")

    def _register_pages(self) -> None:
        """Create and register the four streamlined pages."""
        page_classes = [
            WelcomePage,
            ArtistSearchPage,
            GenerateAlbumLayoutPage,
            FinishPage,
        ]
        for page_cls in page_classes:
            page = page_cls(self._container)
            self.setPage(page_cls.PAGE_ID, page)

    def _on_page_changed(self, page_id: int) -> None:
        """Refresh wizard button labels when the active page changes."""
        if page_id == PageId.EXPORT:
            finish_button = self.button(QWizard.WizardButton.FinishButton)
            finish_button.setText(
                finish_button_label(export_completed=self.session.export_completed)
            )

    def set_window_icon(self, icon: QIcon) -> None:
        """Apply a window icon from compiled resources or assets."""
        self.setWindowIcon(icon)
