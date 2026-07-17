"""Tests for application bootstrap."""

from __future__ import annotations

from vinylsplit import __app_name__, __version__
from vinylsplit.app import create_application, create_wizard
from vinylsplit.wizard.pages.page_ids import PageId


def test_package_metadata() -> None:
    assert __version__ == "1.1.0"
    assert "VinylSplit" in __app_name__


def test_create_application(qapp) -> None:
    app = create_application([])
    assert app.applicationName() == __app_name__
    assert app.applicationVersion() == __version__


def test_wizard_has_seven_pages(container) -> None:
    wizard = create_wizard(container)
    assert wizard.page(PageId.OPEN) is not None
    assert wizard.page(PageId.RELEASE) is not None
    assert wizard.page(PageId.ALIGN) is not None
    assert wizard.page(PageId.EXPORT) is not None
    assert wizard.startId() == PageId.OPEN


def test_wizard_page_titles(container) -> None:
    wizard = create_wizard(container)
    expected_titles = [
        "Open album",
        "Find release",
        "Align & hand off",
        "Export",
    ]
    for page_id, title in zip(range(4), expected_titles, strict=True):
        assert wizard.page(page_id).title() == title