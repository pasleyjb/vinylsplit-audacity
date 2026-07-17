"""Persistent application settings backed by QSettings."""

from __future__ import annotations

from PySide6.QtCore import QSettings

from vinylsplit import __app_name__, __version__


class Settings:
    """Thin wrapper around QSettings for typed, discoverable configuration.

    Settings are stored per-user and per-organization. Additional keys can be
    added here as features are implemented (e.g. MusicBrainz rate limits,
    default export paths, Audacity executable location).
    """

    ORGANIZATION = "VinylSplit"
    APPLICATION = "VinylSplitForAudacity"

    # Setting keys
    KEY_WINDOW_GEOMETRY = "window/geometry"
    KEY_WINDOW_STATE = "window/state"
    KEY_LAST_ARTIST = "wizard/last_artist"
    KEY_LAST_ALBUM = "wizard/last_album"
    KEY_LAST_OPEN_DIR = "wizard/last_open_dir"
    KEY_LAST_EXPORT_DIR = "wizard/last_export_dir"
    KEY_LOG_LEVEL = "logging/level"

    def __init__(self) -> None:
        self._qsettings = QSettings(self.ORGANIZATION, self.APPLICATION)

    @property
    def qsettings(self) -> QSettings:
        """Expose the underlying QSettings for advanced use."""
        return self._qsettings

    def get(self, key: str, default: object = None) -> object:
        """Read a setting value, returning *default* when unset."""
        return self._qsettings.value(key, default)

    def set(self, key: str, value: object) -> None:
        """Persist a setting value."""
        self._qsettings.setValue(key, value)

    def remove(self, key: str) -> None:
        """Remove a setting key."""
        self._qsettings.remove(key)

    def sync(self) -> None:
        """Flush pending changes to persistent storage."""
        self._qsettings.sync()

    @property
    def app_display_name(self) -> str:
        """Human-readable application name including version."""
        return f"{__app_name__} {__version__}"
