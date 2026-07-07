"""Audacity connection verification for the wizard UI."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass

from vinylsplit.audacity.client import (
    AudacityClient,
    AudacityClientConfig,
    AudacityError,
)

_logger = logging.getLogger(__name__)

_BATCH_TRAILER = re.compile(r"^BatchCommand finished:.*$", re.MULTILINE)
_VALID_HELP_MARKERS = ("Help", '"id":"Help"', '"id": "Help"')


@dataclass(frozen=True)
class AudacityConnectionResult:
    """Outcome of an Audacity connectivity check."""

    success: bool
    message: str


def verify_audacity_connection(
    client_factory: Callable[[], AudacityClient] | None = None,
) -> AudacityConnectionResult:
    """Connect to Audacity, run ``Help:``, and report the result.

    Args:
        client_factory: Optional factory used to construct the client. When
            omitted, a default :class:`~vinylsplit.audacity.client.AudacityClient`
            is created for the check.

    Returns:
        :class:`AudacityConnectionResult` with a user-facing message.
    """
    factory = client_factory or _default_client_factory
    client = factory()

    try:
        client.connect()
        response = client.execute("Help:")
        if not _is_valid_help_response(response):
            return AudacityConnectionResult(
                success=False,
                message="Audacity returned an unexpected Help response.",
            )

        major_version = _fetch_major_version(client)
        return AudacityConnectionResult(
            success=True,
            message=f"Connected to Audacity {major_version}.x",
        )
    except AudacityError as exc:
        _logger.warning("Audacity connection check failed: %s", exc)
        return AudacityConnectionResult(success=False, message=str(exc))
    finally:
        client.disconnect()


def _default_client_factory() -> AudacityClient:
    """Create a client with UI-friendly timeouts."""
    config = AudacityClientConfig(connect_timeout=10.0, read_timeout=30.0)
    return AudacityClient(config=config)


def _is_valid_help_response(response: str) -> bool:
    """Return True when *response* looks like a successful Help reply."""
    if not response.strip():
        return False
    if not _BATCH_TRAILER.search(response):
        return False
    return any(marker in response for marker in _VALID_HELP_MARKERS)


def _fetch_major_version(client: AudacityClient) -> str:
    """Read Audacity's major version, falling back to ``3`` when unavailable."""
    try:
        response = client.execute("GetPreference: Name=/Version/Major")
        major = _parse_simple_value(response)
        if major:
            return major
    except AudacityError as exc:
        _logger.debug("Could not read Audacity major version: %s", exc)
    return "3"


def _parse_simple_value(response: str) -> str:
    """Extract the primary value from a simple pipe response."""
    for line in response.splitlines():
        if line.startswith("BatchCommand"):
            continue
        stripped = line.strip()
        if stripped:
            return stripped
    return ""
