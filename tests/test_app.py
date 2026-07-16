"""Tests for application bootstrap."""

from __future__ import annotations

from vinylsplit import __app_name__, __version__
from vinylsplit.app import create_application, create_wizard
from vinylsplit.wizard.pages.page_ids import PageId


def test_package_metadata() -> None:
    assert __version__ == "1.0.0"
    assert "VinylSplit" in __app_name__


def test_create_application(qapp) -> None:
    app = create_application([])
    assert app.applicationName() == __app_name__
    assert app.applicationVersion() == __version__


def test_wizard_has_seven_pages(container) -> None:
    wizard = create_wizard(container)
    assert wizard.page(PageId.WELCOME) is not None
    assert wizard.page(PageId.GENERATE_ALBUM_LAYOUT) is not None
    assert wizard.page(PageId.FINISH) is not None
    assert wizard.startId() == PageId.WELCOME


def test_wizard_page_titles(container) -> None:
    wizard = create_wizard(container)
    expected_titles = [
        "Welcome",
        "Artist & Album Search",
        "Release Selection",
        "Track List",
        "Generate Album Layout",
        "Review Album Layout",
        "Finish",
    ]
    for page_id, title in zip(range(7), expected_titles, strict=True):
        assert wizard.page(page_id).title() == title