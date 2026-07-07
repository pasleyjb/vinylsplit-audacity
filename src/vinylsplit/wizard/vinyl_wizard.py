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
    ReleaseSelectionPage,
    ReviewPage,
    TrackListPage,
    WelcomePage,
)
from vinylsplit.wizard.pages.page_ids import PageId


class VinylSplitWizard(QWizard):
    """Seven-step wizard guiding the vinyl digitization workflow.

    Pages are registered in workflow order. Each page is a reusable
    :class:`~vinylsplit.wizard.pages.base.WizardPageBase` subclass that
    receives the dependency injection container.
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

        self._register_pages()
        self._configure_navigation()

        self._logger.info("Wizard initialized with %d pages", PageId.FINISH + 1)

    @property
    def container(self) -> Container:
        """Dependency injection container shared by all pages."""
        return self._container

    @property
    def session(self) -> WizardSession:
        """Wizard session state for the active workflow."""
        return self._container.session

    def _register_pages(self) -> None:
        """Create and register all wizard pages."""
        page_classes = [
            WelcomePage,
            ArtistSearchPage,
            ReleaseSelectionPage,
            TrackListPage,
            GenerateAlbumLayoutPage,
            ReviewPage,
            FinishPage,
        ]

        for page_cls in page_classes:
            page = page_cls(self._container)
            self.setPage(page_cls.PAGE_ID, page)

    def _configure_navigation(self) -> None:
        """Set linear page flow for v0.1.

        Pages use sequential :class:`~vinylsplit.wizard.pages.page_ids.PageId`
        values so QWizard's default ``nextId()`` advances 0 → 6 in order.
        """
        self.setStartId(PageId.WELCOME)

    def set_window_icon(self, icon: QIcon) -> None:
        """Apply a window icon from compiled resources or assets."""
        self.setWindowIcon(icon)