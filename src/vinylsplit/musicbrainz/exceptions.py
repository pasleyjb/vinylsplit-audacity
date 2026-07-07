"""MusicBrainz client exceptions."""


class MusicBrainzError(Exception):
    """Base exception for MusicBrainz client errors."""


class MusicBrainzNetworkError(MusicBrainzError):
    """Raised when the network is unavailable or unreachable."""


class MusicBrainzTimeoutError(MusicBrainzError):
    """Raised when a MusicBrainz request exceeds its timeout."""


class MusicBrainzAPIError(MusicBrainzError):
    """Raised when MusicBrainz returns an unexpected HTTP response."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
