"""Application entry point for VinylSplit for Audacity."""

from __future__ import annotations

import logging
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from vinylsplit import __app_name__, __version__
from vinylsplit.core.container import Container
from vinylsplit.core.logging_config import configure_logging
from vinylsplit.core.settings import Settings
from vinylsplit.wizard import VinylSplitWizard

logger = logging.getLogger(__name__)


def create_application(argv: list[str] | None = None) -> QApplication:
    """Create and configure the Qt application instance.

    If a :class:`QApplication` already exists (e.g. in tests), its metadata is
    updated and the existing instance is returned.

    Args:
        argv: Command-line arguments. Defaults to ``sys.argv``.

    Returns:
        A configured :class:`QApplication` ready for event loop execution.
    """
    existing = QApplication.instance()
    if existing is not None:
        app = existing
    else:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        app = QApplication(argv or sys.argv)

    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(Settings.ORGANIZATION)
    app.setOrganizationDomain("vinylsplit.github.io")
    return app


def create_wizard(container: Container | None = None) -> VinylSplitWizard:
    """Construct the main wizard window.

    Args:
        container: Optional pre-built DI container. A default container is
            created when omitted.

    Returns:
        The configured :class:`~vinylsplit.wizard.VinylSplitWizard`.
    """
    return VinylSplitWizard(container or Container())


def main(argv: list[str] | None = None) -> int:
    """Launch VinylSplit for Audacity.

    Args:
        argv: Command-line arguments passed to Qt.

    Returns:
        Process exit code from the Qt event loop.
    """
    configure_logging()
    logger.info("Launching application")

    app = create_application(argv)
    container = Container()
    wizard = create_wizard(container)
    wizard.show()

    exit_code = app.exec()
    container.settings.sync()
    logger.info("Application exited with code %d", exit_code)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
