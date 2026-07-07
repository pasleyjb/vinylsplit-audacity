"""Base class for VinylSplit wizard pages."""

from __future__ import annotations

import logging
from typing import ClassVar

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWizardPage

from vinylsplit.core.container import Container
from vinylsplit.metadata.session import WizardSession
from vinylsplit.wizard.ui_style import apply_page_layout, create_info_banner


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
        apply_page_layout(self._layout)
        self.setLayout(self._layout)
        self.build_content()
        self._add_page_stretch()

    @property
    def container(self) -> Container:
        """Dependency injection container for this page."""
        return self._container

    @property
    def session(self) -> WizardSession:
        """Wizard session state for cross-page communication."""
        return self._container.session

    def build_content(self) -> None:
        """Build page content. Override in subclasses."""
        self._layout.addWidget(self._create_body_label())

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

    def _create_body_label(self, text: str | None = None) -> QLabel:
        """Create a styled body copy label."""
        if text is None:
            label = create_info_banner(
                f"<b>{self.PAGE_TITLE}</b><br>"
                "Content for this step is not available."
            )
            return label
        label = QLabel(text)
        label.setWordWrap(True)
        font = QFont()
        font.setPointSize(10)
        label.setFont(font)
        return label

    def _create_info_banner(self, text: str) -> QLabel:
        """Create a highlighted instruction banner."""
        return create_info_banner(text)

    def _create_placeholder_label(self, text: str) -> QLabel:
        """Backward-compatible alias used by older page implementations."""
        if text.strip():
            return self._create_info_banner(text)
        label = QLabel("")
        label.setWordWrap(True)
        return label

    def _add_page_stretch(self) -> None:
        """Allow subclasses to opt out by setting ``_use_page_stretch = False``."""
        if getattr(self, "_use_page_stretch", True):
            self._layout.addStretch(1)

    def initializePage(self) -> None:
        """Called when the page is entered. Override to refresh data."""
        self._logger.debug("Entering page: %s (id=%s)", self.PAGE_TITLE, self.PAGE_ID)
        super().initializePage()

    def cleanupPage(self) -> None:
        """Called when leaving the page. Override to persist state."""
        self._logger.debug("Leaving page: %s (id=%s)", self.PAGE_TITLE, self.PAGE_ID)
        super().cleanupPage()