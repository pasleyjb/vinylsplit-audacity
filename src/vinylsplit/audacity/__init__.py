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
from vinylsplit.audacity.import_audio import (
    AudacityProjectProbe,
    import_audio_file,
    probe_audacity_project,
    seed_queries_from_track_names,
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
    "AudacityProjectProbe",
    "AudacityTimeoutError",
    "PipePaths",
    "detect_pipe_paths",
    "import_audio_file",
    "probe_audacity_project",
    "seed_queries_from_track_names",
    "verify_audacity_connection",
]
