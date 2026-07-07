"""Lightweight dependency injection container for service wiring."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, TypeVar

from vinylsplit.core.settings import Settings

T = TypeVar("T")
Factory = Callable[["Container"], T]


class Container:
    """Register and resolve application services by type or name.

    The container supports lazy singleton registration so services are created
    on first access. Future modules (MusicBrainz client, Audacity bridge,
    metadata store) register here instead of constructing dependencies inline.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._singletons: dict[str, Any] = {}
        self._factories: dict[str, Factory[Any]] = {}
        self._logger = logging.getLogger(__name__)

        self._register_defaults()

    @property
    def settings(self) -> Settings:
        """Application settings service."""
        return self._settings

    def register_singleton(self, name: str, factory: Factory[T]) -> None:
        """Register a lazy singleton factory under *name*."""
        self._factories[name] = factory

    def resolve(self, name: str) -> Any:
        """Resolve a registered service, creating it on first access."""
        if name not in self._singletons:
            if name not in self._factories:
                msg = f"Service '{name}' is not registered."
                raise KeyError(msg)
            self._logger.debug("Creating service: %s", name)
            self._singletons[name] = self._factories[name](self)
        return self._singletons[name]

    def _register_defaults(self) -> None:
        """Register built-in services available in v0.1."""
        self.register_singleton("settings", lambda c: c.settings)

        # Placeholder registrations for future modules.
        # Uncomment and implement when the respective packages are ready:
        #
        # self.register_singleton("musicbrainz", lambda c: MusicBrainzClient(...))
        # self.register_singleton("audacity", lambda c: AudacityBridge(...))
        # self.register_singleton("metadata", lambda c: MetadataStore(...))
