"""Tests for the Welcome wizard page."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt

from vinylsplit.audacity.connection import AudacityConnectionResult
from vinylsplit.wizard.pages.welcome_page import (
    _STATUS_CONNECTED,
    _STATUS_NOT_CONNECTED,
    WelcomePage,
)


@pytest.fixture
def welcome_page(container) -> WelcomePage:
    """Provide a welcome page with a synchronous connection verifier."""

    def verifier() -> AudacityConnectionResult:
        return AudacityConnectionResult(
            success=True, message="Connected to Audacity 3.x"
        )

    page = WelcomePage(container, connection_verifier=verifier)
    page.show()
    return page


def test_welcome_page_shows_not_connected_initially(container) -> None:
    page = WelcomePage(
        container, connection_verifier=lambda: AudacityConnectionResult(False, "")
    )

    assert page._status_label.text() == _STATUS_NOT_CONNECTED
    assert page.is_audacity_connected() is False
    assert page._connect_button.text() == "Connect"


def test_apply_connection_result_success(
    welcome_page: WelcomePage, session
) -> None:
    welcome_page.apply_connection_result(
        AudacityConnectionResult(success=True, message="Connected to Audacity 3.x")
    )

    assert welcome_page._status_label.text() == _STATUS_CONNECTED
    assert welcome_page._message_label.text() == "Connected to Audacity 3.x"
    assert welcome_page.is_audacity_connected() is True
    assert session.audacity_connected is True
    assert session.validation_errors == []


def test_apply_connection_result_failure(container, session) -> None:
    page = WelcomePage(
        container, connection_verifier=lambda: AudacityConnectionResult(False, "")
    )

    page.apply_connection_result(
        AudacityConnectionResult(success=False, message="Pipes are not available.")
    )

    assert page._status_label.text() == _STATUS_NOT_CONNECTED
    assert page._message_label.text() == "Pipes are not available."
    assert page.is_audacity_connected() is False
    assert session.audacity_connected is False
    assert "Pipes are not available." in session.validation_errors


def test_connect_button_updates_ui(qtbot, container) -> None:
    results = [
        AudacityConnectionResult(success=True, message="Connected to Audacity 3.x"),
    ]

    def verifier() -> AudacityConnectionResult:
        return results.pop(0)

    page = WelcomePage(container, connection_verifier=verifier)
    qtbot.addWidget(page)

    qtbot.mouseClick(page._connect_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: page._status_label.text() == _STATUS_CONNECTED, timeout=2000
    )

    assert page._message_label.text() == "Connected to Audacity 3.x"
    assert page.is_audacity_connected() is True
    assert page._connect_button.isEnabled() is True


def test_connect_button_shows_error_message(qtbot, container) -> None:
    def verifier() -> AudacityConnectionResult:
        return AudacityConnectionResult(
            success=False,
            message="Audacity mod-script-pipe endpoints are not available.",
        )

    page = WelcomePage(container, connection_verifier=verifier)
    qtbot.addWidget(page)

    qtbot.mouseClick(page._connect_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: "not available" in page._message_label.text(),
        timeout=2000,
    )

    assert page._status_label.text() == _STATUS_NOT_CONNECTED
    assert page.is_audacity_connected() is False
