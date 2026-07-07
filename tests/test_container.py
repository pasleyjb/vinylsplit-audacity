"""Tests for the dependency injection container."""

from __future__ import annotations

import pytest

from vinylsplit.audacity.client import AudacityClient
from vinylsplit.core.container import Container
from vinylsplit.core.settings import Settings
from vinylsplit.metadata.session import WizardSession
from vinylsplit.musicbrainz.client import MusicBrainzClient


def test_settings_singleton(container: Container) -> None:
    settings_a = container.resolve("settings")
    settings_b = container.resolve("settings")
    assert settings_a is settings_b
    assert isinstance(settings_a, Settings)


def test_resolve_unknown_service_raises(container: Container) -> None:
    with pytest.raises(KeyError, match="not registered"):
        container.resolve("nonexistent")


def test_session_injected_via_container(container: Container) -> None:
    assert isinstance(container.session, WizardSession)


def test_session_not_registered_as_singleton(container: Container) -> None:
    with pytest.raises(KeyError, match="not registered"):
        container.resolve("session")


def test_musicbrainz_and_audacity_registered(container: Container) -> None:
    assert isinstance(container.resolve("musicbrainz"), MusicBrainzClient)
    assert isinstance(container.resolve("audacity"), AudacityClient)


def test_injected_session_is_shared_across_container_property(
    settings: Settings,
) -> None:
    session = WizardSession()
    container = Container(settings=settings, session=session)
    assert container.session is session
