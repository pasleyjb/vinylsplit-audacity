"""Welcome wizard page."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import ClassVar

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget, QWizardPage

from vinylsplit.audacity.connection import (
    AudacityConnectionResult,
    verify_audacity_connection,
)
from vinylsplit.core.container import Container
from vinylsplit.wizard.pages.base import WizardPageBase
from vinylsplit.wizard.pages.page_ids import PageId
from vinylsplit.wizard.ui_style import (
    connection_status_text,
    create_section_group,
    create_status_label,
    style_primary_button,
)

_logger = logging.getLogger(__name__)

_STATUS_CONNECTED = connection_status_text(connected=True)
_STATUS_NOT_CONNECTED = connection_status_text(connected=False)


class _ConnectionWorker(QThread):
    """Run Audacity verification off the UI thread."""

    finished = Signal(object)

    def __init__(
        self,
        verifier: Callable[[], AudacityConnectionResult],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._verifier = verifier

    def run(self) -> None:
        self.finished.emit(self._verifier())


class WelcomePage(WizardPageBase):
    """Introduce the application and outline the digitization workflow."""

    PAGE_ID: ClassVar[int] = PageId.WELCOME
    PAGE_TITLE: ClassVar[str] = "Welcome"
    PAGE_SUBTITLE: ClassVar[str] = (
        "Generate a complete album layout in Audacity from MusicBrainz metadata."
    )

    def __init__(
        self,
        container: Container,
        parent: QWizardPage | None = None,
        *,
        connection_verifier: Callable[[], AudacityConnectionResult] | None = None,
    ) -> None:
        self._connection_verifier = connection_verifier or verify_audacity_connection
        self._connection_worker: _ConnectionWorker | None = None
        super().__init__(container, parent)

    def build_content(self) -> None:
        self._layout.addWidget(
            self._create_info_banner(
                "<b>Welcome to VinylSplit for Audacity</b><br><br>"
                "This wizard will guide you through:<br>"
                "<ol>"
                "<li>Search MusicBrainz and select your release</li>"
                "<li>Review the official track listing</li>"
                "<li>Generate track regions in Audacity</li>"
                "<li>Adjust boundaries and refresh the layout</li>"
                "<li>Export tagged tracks with album artwork</li>"
                "</ol>"
                "Connect to Audacity below, then click <b>Next</b>."
            )
        )

        self._layout.addWidget(self._build_audacity_connection_section())

    def _build_audacity_connection_section(self) -> QWidget:
        """Build the Audacity connection status and controls."""
        section = create_section_group("Audacity Connection")
        layout = QVBoxLayout(section)
        layout.setSpacing(10)

        self._status_label = create_status_label(tone="neutral")
        self._status_label.setText(_STATUS_NOT_CONNECTED)

        self._connect_button = QPushButton()
        style_primary_button(self._connect_button, "Connect")
        self._connect_button.clicked.connect(self._on_connect_clicked)

        self._message_label = QLabel("")
        self._message_label.setWordWrap(True)
        self._message_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        layout.addWidget(self._status_label)
        layout.addWidget(self._connect_button)
        layout.addWidget(self._message_label)
        return section

    def _on_connect_clicked(self) -> None:
        """Start an Audacity connectivity check."""
        if self._connection_worker is not None and self._connection_worker.isRunning():
            return

        self._connect_button.setEnabled(False)
        self._message_label.setText("Connecting to Audacity...")
        self._update_status_label(connected=False)

        self._connection_worker = _ConnectionWorker(self._connection_verifier, self)
        self._connection_worker.finished.connect(self._on_connection_finished)
        self._connection_worker.start()

    def _on_connection_finished(self, result: AudacityConnectionResult) -> None:
        """Apply the connectivity result to the page UI."""
        self._connect_button.setEnabled(True)
        self._connection_worker = None
        self.apply_connection_result(result)

    def initializePage(self) -> None:
        super().initializePage()
        self._update_status_label(connected=self.session.audacity_connected)

    def apply_connection_result(self, result: AudacityConnectionResult) -> None:
        """Update UI labels from a connectivity result (also used in tests)."""
        self.session.set_audacity_connected(result.success)
        self._update_status_label(connected=result.success)
        self._message_label.setText(result.message)

        if result.success:
            self.session.clear_validation_errors()
            _logger.info("Audacity connection verified: %s", result.message)
        else:
            self.session.add_validation_error(result.message)
            _logger.warning("Audacity connection failed: %s", result.message)

    def _update_status_label(self, *, connected: bool) -> None:
        self._status_label.setText(
            _STATUS_CONNECTED if connected else _STATUS_NOT_CONNECTED
        )
        self._status_label.setObjectName(
            "StatusSuccess" if connected else "StatusError"
        )
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

    def is_audacity_connected(self) -> bool:
        """Return whether Audacity communication is available."""
        return self.session.audacity_connected