"""Base class for VinylSplit wizard pages."""

from __future__ import annotations

import logging
from typing import ClassVar

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWizardPage

from vinylsplit.core.container import Container


class WizardPageBase(QWizardPage):
    """Reusable base for all wizard pages.

    Subclasses declare ``PAGE_ID``, ``PAGE_TITLE``, and optionally
    ``PAGE_SUBTITLE``. Override :meth:`build_content` to add page-specific
    widgets. Pages receive a :class:`~vinylsplit.core.container.Container`
    for dependency access.

    This class is Qt Designer compatible: promote a ``QWizardPage`` widget
    to ``WizardPageBase`` and load a ``.ui`` file via :meth:`load_ui` in a
    subclass.
    """

    PAGE_ID: ClassVar[int]
    PAGE_TITLE: ClassVar[str]
    PAGE_SUBTITLE: ClassVar[str] = ""

    def __init__(self, container: Container, parent: QWizardPage | None = None) -> None:
        super().__init__(parent)
        self._container = container
        self._logger = logging.getLogger(self.__class__.__module__)

        self.setTitle(self.PAGE_TITLE)
        if self.PAGE_SUBTITLE:
            self.setSubTitle(self.PAGE_SUBTITLE)

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)
        self.build_content()

    @property
    def container(self) -> Container:
        """Dependency injection container for this page."""
        return self._container

    def build_content(self) -> None:
        """Build page content. Override in subclasses."""
        self._layout.addWidget(self._create_placeholder_label())

    def load_ui(self, ui_path: str) -> None:
        """Load a Qt Designer ``.ui`` file into this page.

        Args:
            ui_path: Path to the ``.ui`` file relative to the ui package
                or an absolute filesystem path.
        """
        from PySide6.QtCore import QFile
        from PySide6.QtUiTools import QUiLoader

        ui_file = QFile(ui_path)
        if not ui_file.open(QFile.OpenModeFlag.ReadOnly):
            msg = f"Cannot open UI file: {ui_path}"
            raise OSError(msg)

        loader = QUiLoader()
        widget = loader.load(ui_file, self)
        ui_file.close()

        if widget is not None:
            self._layout.addWidget(widget)

    def _create_placeholder_label(self, text: str | None = None) -> QLabel:
        """Create a styled placeholder label for v0.1 pages."""
        label = QLabel(text or self._default_placeholder_text())
        label.setWordWrap(True)
        font = QFont()
        font.setPointSize(11)
        label.setFont(font)
        return label

    def _default_placeholder_text(self) -> str:
        """Default placeholder copy for unimplemented page content."""
        return (
            f"<b>{self.PAGE_TITLE}</b><br><br>"
            "This step is a placeholder in version 0.1. "
            "Functionality will be added in a future release."
        )

    def initializePage(self) -> None:
        """Called when the page is entered. Override to refresh data."""
        self._logger.debug("Entering page: %s (id=%s)", self.PAGE_TITLE, self.PAGE_ID)
        super().initializePage()

    def cleanupPage(self) -> None:
        """Called when leaving the page. Override to persist state."""
        self._logger.debug("Leaving page: %s (id=%s)", self.PAGE_TITLE, self.PAGE_ID)
        super().cleanupPage()
