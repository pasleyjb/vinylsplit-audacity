"""Tests for Audacity connection verification."""

from __future__ import annotations

from vinylsplit.audacity.client import AudacityConnectionError, AudacityError
from vinylsplit.audacity.connection import (
    AudacityConnectionResult,
    verify_audacity_connection,
)

_VALID_HELP_RESPONSE = '{ "id":"Help", "name":"Help" }\nBatchCommand finished: OK\n\n'


class _FakeClient:
    """Minimal stand-in for :class:`~vinylsplit.audacity.client.AudacityClient`."""

    def __init__(
        self,
        *,
        help_response: str = _VALID_HELP_RESPONSE,
        major_version: str = "3",
        connect_error: Exception | None = None,
        help_error: Exception | None = None,
        version_error: Exception | None = None,
    ) -> None:
        self.help_response = help_response
        self.major_version = major_version
        self.connect_error = connect_error
        self.help_error = help_error
        self.version_error = version_error
        self.connected = False
        self.disconnected = False

    def connect(self) -> None:
        if self.connect_error is not None:
            raise self.connect_error
        self.connected = True

    def disconnect(self) -> None:
        self.disconnected = True

    def execute(self, command: str) -> str:
        if command == "Help:":
            if self.help_error is not None:
                raise self.help_error
            return self.help_response
        if command == "GetPreference: Name=/Version/Major":
            if self.version_error is not None:
                raise self.version_error
            return f"{self.major_version}\nBatchCommand finished: OK\n\n"
        msg = f"Unexpected command: {command}"
        raise AssertionError(msg)


def test_verify_connection_success() -> None:
    fake = _FakeClient(major_version="3")

    result = verify_audacity_connection(client_factory=lambda: fake)

    assert result == AudacityConnectionResult(
        success=True,
        message="Connected to Audacity 3.x",
    )
    assert fake.connected is True
    assert fake.disconnected is True


def test_verify_connection_returns_error_message() -> None:
    fake = _FakeClient(
        connect_error=AudacityConnectionError("Pipes are not available."),
    )

    result = verify_audacity_connection(client_factory=lambda: fake)

    assert result.success is False
    assert result.message == "Pipes are not available."
    assert fake.disconnected is True


def test_verify_connection_invalid_help_response() -> None:
    fake = _FakeClient(help_response="Unexpected payload\n")

    result = verify_audacity_connection(client_factory=lambda: fake)

    assert result.success is False
    assert "unexpected Help response" in result.message


def test_verify_connection_falls_back_when_version_unavailable() -> None:
    fake = _FakeClient(version_error=AudacityError("preference unavailable"))

    result = verify_audacity_connection(client_factory=lambda: fake)

    assert result.success is True
    assert result.message == "Connected to Audacity 3.x"


def test_verify_connection_help_execute_failure() -> None:
    fake = _FakeClient(help_error=AudacityConnectionError("Timed out waiting."))

    result = verify_audacity_connection(client_factory=lambda: fake)

    assert result.success is False
    assert result.message == "Timed out waiting."
