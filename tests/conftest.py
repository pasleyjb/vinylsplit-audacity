"""Shared pytest fixtures."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from vinylsplit.core.container import Container
from vinylsplit.core.settings import Settings


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    """Provide a session-scoped QApplication for Qt widget tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def settings(qapp: QApplication) -> Settings:
    """Provide an isolated Settings instance."""
    return Settings()


@pytest.fixture
def container(settings: Settings) -> Container:
    """Provide a DI container wired to test settings."""
    return Container(settings=settings)
