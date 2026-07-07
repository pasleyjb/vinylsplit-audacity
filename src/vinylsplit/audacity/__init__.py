"""Audacity integration layer.

This package provides bridges to Audacity via mod-script-pipe for reading and
writing label tracks and triggering export operations.
"""

from vinylsplit.audacity.client import (
    AudacityClient,
    AudacityClientConfig,
    AudacityCommandError,
    AudacityConnectionError,
    AudacityError,
    AudacityNotConnectedError,
    AudacityPipeBrokenError,
    AudacityTimeoutError,
    PipePaths,
    detect_pipe_paths,
)
from vinylsplit.audacity.connection import (
    AudacityConnectionResult,
    verify_audacity_connection,
)

__all__ = [
    "AudacityClient",
    "AudacityClientConfig",
    "AudacityCommandError",
    "AudacityConnectionError",
    "AudacityConnectionResult",
    "AudacityError",
    "AudacityNotConnectedError",
    "AudacityPipeBrokenError",
    "AudacityTimeoutError",
    "PipePaths",
    "detect_pipe_paths",
    "verify_audacity_connection",
]
