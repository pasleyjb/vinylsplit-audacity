"""Tests for the dependency injection container."""

from __future__ import annotations

import pytest

from vinylsplit.core.container import Container
from vinylsplit.core.settings import Settings


def test_settings_singleton(container: Container) -> None:
    settings_a = container.resolve("settings")
    settings_b = container.resolve("settings")
    assert settings_a is settings_b
    assert isinstance(settings_a, Settings)


def test_resolve_unknown_service_raises(container: Container) -> None:
    with pytest.raises(KeyError, match="not registered"):
        container.resolve("nonexistent")
