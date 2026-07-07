"""Audacity mod-script-pipe client.

Communicates with a running Audacity instance through named pipes (FIFOs on
Linux/macOS, named pipes on Windows). Requires the mod-script-pipe module to
be enabled in Audacity preferences.

Reference implementation:
https://github.com/audacity/audacity/tree/master/au3/scripts/piped-work
"""

from __future__ import annotations

import logging
import os
import re
import sys
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class AudacityError(Exception):
    """Base exception for Audacity client errors."""


class AudacityConnectionError(AudacityError):
    """Raised when pipes are missing or cannot be opened."""


class AudacityNotConnectedError(AudacityError):
    """Raised when an operation requires an active connection."""


class AudacityPipeBrokenError(AudacityError):
    """Raised when Audacity closes or crashes during communication."""


class AudacityTimeoutError(AudacityError):
    """Raised when an operation exceeds its configured timeout."""


class AudacityCommandError(AudacityError):
    """Raised when Audacity reports command failure."""

    def __init__(self, message: str, *, response: str) -> None:
        super().__init__(message)
        self.response = response


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_BATCH_FINISHED_OK = re.compile(r"BatchCommand finished:\s*OK!?", re.IGNORECASE)
_BATCH_FINISHED_FAILED = re.compile(r"BatchCommand finished:\s*Failed", re.IGNORECASE)


@dataclass(frozen=True)
class PipePaths:
    """Named pipe locations for bidirectional Audacity communication."""

    to_pipe: Path
    from_pipe: Path


@dataclass
class AudacityClientConfig:
    """Timeouts and optional overrides for :class:`AudacityClient`.

    Attributes:
        connect_timeout: Seconds to wait while opening each pipe.
        read_timeout: Seconds to wait for each response line.
        pipe_paths: Explicit pipe paths. When *None*, paths are detected for
            the current platform automatically.
    """

    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    pipe_paths: PipePaths | None = None


# ---------------------------------------------------------------------------
# Pipe path detection
# ---------------------------------------------------------------------------


def detect_pipe_paths() -> PipePaths:
    """Return mod-script-pipe paths for the current platform.

    On Linux the pipes live under ``/tmp`` and include the user ID, matching
    Audacity's default mod-script-pipe layout.

    Returns:
        Resolved :class:`PipePaths` for the running user.

    Raises:
        AudacityConnectionError: If the platform is unsupported.
    """
    if sys.platform == "win32":
        return PipePaths(
            to_pipe=Path(r"\\.\pipe\ToSrvPipe"),
            from_pipe=Path(r"\\.\pipe\FromSrvPipe"),
        )

    if sys.platform == "darwin":
        uid = os.getuid()
        base = Path("/tmp")
        return PipePaths(
            to_pipe=base / f"audacity_script_pipe.to.{uid}",
            from_pipe=base / f"audacity_script_pipe.from.{uid}",
        )

    if sys.platform.startswith("linux") or sys.platform == "linux":
        uid = os.getuid()
        base = Path("/tmp")
        return PipePaths(
            to_pipe=base / f"audacity_script_pipe.to.{uid}",
            from_pipe=base / f"audacity_script_pipe.from.{uid}",
        )

    msg = f"Unsupported platform for mod-script-pipe: {sys.platform}"
    raise AudacityConnectionError(msg)


def _command_terminator() -> str:
    """Return the end-of-line sequence expected by mod-script-pipe."""
    if sys.platform == "win32":
        return "\r\n\0"
    return "\n"


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


@dataclass
class AudacityClient:
    """Reusable client for Audacity mod-script-pipe commands.

    Typical usage::

        client = AudacityClient()
        client.connect()
        try:
            print(client.help())
            print(client.execute('GetInfo: Type=Labels Format=LISP'))
        finally:
            client.disconnect()

    The client is intentionally free of global state so it can be constructed,
    configured, and injected through :class:`~vinylsplit.core.container.Container`
    in later versions.

    Args:
        config: Optional timeouts and pipe overrides.
        opener: Callable used to open pipe files (overridable in tests).
    """

    config: AudacityClientConfig = field(default_factory=AudacityClientConfig)
    opener: Callable[[Path, str], TextIO] = field(default=open, repr=False)

    _pipe_paths: PipePaths = field(init=False)
    _to_file: TextIO | None = field(default=None, init=False, repr=False)
    _from_file: TextIO | None = field(default=None, init=False, repr=False)
    _connected: bool = field(default=False, init=False, repr=False)
    _logger: logging.Logger = field(
        default_factory=lambda: logging.getLogger(__name__),
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        self._pipe_paths = self.config.pipe_paths or detect_pipe_paths()

    # -- Connection lifecycle ------------------------------------------------

    def connect(self) -> None:
        """Open the to/from pipes and mark the client as connected.

        Raises:
            AudacityConnectionError: When pipes are missing or cannot open.
            AudacityTimeoutError: When opening a pipe exceeds ``connect_timeout``.
        """
        if self._connected:
            self._logger.debug("Already connected to Audacity pipes.")
            return

        self._validate_pipes_exist()

        self._logger.info(
            "Connecting to Audacity pipes (to=%s, from=%s)",
            self._pipe_paths.to_pipe,
            self._pipe_paths.from_pipe,
        )

        # Audacity expects the write pipe to be opened before the read pipe.
        self._to_file = self._open_with_timeout(
            self._pipe_paths.to_pipe,
            "w",
            timeout=self.config.connect_timeout,
        )
        self._from_file = self._open_with_timeout(
            self._pipe_paths.from_pipe,
            "r",
            timeout=self.config.connect_timeout,
        )
        self._connected = True
        self._logger.info("Connected to Audacity mod-script-pipe.")

    def disconnect(self) -> None:
        """Close open pipes and release the connection."""
        self._close_file(self._to_file, "write")
        self._close_file(self._from_file, "read")
        self._to_file = None
        self._from_file = None
        self._connected = False
        self._logger.info("Disconnected from Audacity mod-script-pipe.")

    def is_connected(self) -> bool:
        """Return ``True`` when both pipes are open."""
        return (
            self._connected
            and self._to_file is not None
            and not self._to_file.closed
            and self._from_file is not None
            and not self._from_file.closed
        )

    # -- Command I/O ---------------------------------------------------------

    def send_command(self, command: str) -> None:
        """Write a single command to Audacity without waiting for a reply.

        Args:
            command: Audacity command text without trailing terminator.

        Raises:
            AudacityNotConnectedError: When :meth:`connect` has not succeeded.
            AudacityPipeBrokenError: When the write pipe is no longer usable.
        """
        self._require_connection()
        assert self._to_file is not None

        payload = command.rstrip("\r\n\0") + _command_terminator()
        self._logger.debug("Sending command: %s", command)

        try:
            self._to_file.write(payload)
            self._to_file.flush()
        except BrokenPipeError as exc:
            self._mark_disconnected()
            msg = "Audacity write pipe closed unexpectedly."
            raise AudacityPipeBrokenError(msg) from exc
        except OSError as exc:
            self._mark_disconnected()
            msg = f"Failed to send command: {exc}"
            raise AudacityPipeBrokenError(msg) from exc

    def read_response(self) -> str:
        """Read one complete response block from Audacity.

        Responses are delimited by a blank line, consistent with Audacity's
        official pipe examples. The raw response string—including the
        ``BatchCommand finished`` trailer—is returned.

        Returns:
            Full multi-line response text from Audacity.

        Raises:
            AudacityNotConnectedError: When :meth:`connect` has not succeeded.
            AudacityTimeoutError: When no response arrives within ``read_timeout``.
            AudacityPipeBrokenError: When the read pipe closes before completion.
        """
        self._require_connection()
        assert self._from_file is not None

        response_lines: list[str] = []
        body_started = False

        while True:
            line = self._readline_with_timeout(self.config.read_timeout)

            if line == "":
                self._mark_disconnected()
                msg = "Audacity read pipe closed before response completed."
                raise AudacityPipeBrokenError(msg)

            if line == "\n" and body_started:
                break

            response_lines.append(line)
            if line.strip():
                body_started = True

        response = "".join(response_lines)
        self._logger.debug(
            "Received response (%d chars): %s",
            len(response),
            _summarize_response(response),
        )
        return response

    def execute(self, command: str) -> str:
        """Send a command and return its validated response.

        Args:
            command: Audacity command text.

        Returns:
            Full response string from Audacity.

        Raises:
            AudacityCommandError: When Audacity reports command failure.
            AudacityError: Subclasses for connection, timeout, or pipe errors.
        """
        self.send_command(command)
        response = self.read_response()
        self._validate_batch_response(response)
        return response

    def help(self, command: str = "Help") -> str:
        """Request inline help from Audacity.

        Args:
            command: Command name to query. The default requests general help.

        Returns:
            Audacity help text for the requested command.
        """
        if command == "Help":
            return self.execute("Help:")
        return self.execute(f'Help: Command="{command}"')

    # -- Internal helpers ----------------------------------------------------

    def _validate_pipes_exist(self) -> None:
        """Ensure both pipe paths are present before attempting to connect."""
        missing: list[Path] = []
        if not self._pipe_paths.to_pipe.exists():
            missing.append(self._pipe_paths.to_pipe)
        if not self._pipe_paths.from_pipe.exists():
            missing.append(self._pipe_paths.from_pipe)

        if missing:
            missing_list = ", ".join(str(path) for path in missing)
            msg = (
                "Audacity mod-script-pipe endpoints are not available: "
                f"{missing_list}. Ensure Audacity is running and "
                "mod-script-pipe is enabled in Preferences → Modules."
            )
            raise AudacityConnectionError(msg)

    def _open_with_timeout(self, path: Path, mode: str, *, timeout: float) -> TextIO:
        """Open a blocking FIFO/pipe with a bounded wait."""
        handle: list[TextIO] = []
        error: list[BaseException] = []

        def target() -> None:
            try:
                handle.append(
                    self.opener(
                        path,
                        mode,
                        encoding="utf-8",
                        newline="\n",
                    )
                )
            except BaseException as exc:  # noqa: BLE001 — capture open failures
                error.append(exc)

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            msg = f"Timed out after {timeout}s opening pipe: {path}"
            raise AudacityTimeoutError(msg)

        if error:
            msg = f"Failed to open pipe {path}: {error[0]}"
            raise AudacityConnectionError(msg) from error[0]

        if not handle:
            msg = f"Failed to open pipe: {path}"
            raise AudacityConnectionError(msg)

        return handle[0]

    def _readline_with_timeout(self, timeout: float) -> str:
        """Read a single line from the response pipe with a timeout."""
        assert self._from_file is not None
        # Use a worker thread for all platforms. ``select`` is unreliable on
        # FIFOs opened in text mode, and Audacity's reference pipeclient blocks
        # on a dedicated reader thread.
        return self._readline_threaded(timeout)

    def _readline_threaded(self, timeout: float) -> str:
        """Read one line on a worker thread so callers never block forever."""
        result: list[str] = []
        error: list[BaseException] = []

        def target() -> None:
            try:
                assert self._from_file is not None
                result.append(self._from_file.readline())
            except BaseException as exc:  # noqa: BLE001
                error.append(exc)

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            msg = f"Timed out after {timeout}s waiting for Audacity response."
            raise AudacityTimeoutError(msg)

        if error:
            raise error[0]

        if not result:
            return ""
        return result[0]

    def _validate_batch_response(self, response: str) -> None:
        """Ensure Audacity reported a completed batch command."""
        if _BATCH_FINISHED_FAILED.search(response):
            msg = "Audacity reported command failure."
            raise AudacityCommandError(msg, response=response)

        if not _BATCH_FINISHED_OK.search(response):
            self._logger.warning(
                "Response missing 'BatchCommand finished: OK!' marker."
            )

    def _require_connection(self) -> None:
        if not self.is_connected():
            msg = "Audacity client is not connected. Call connect() first."
            raise AudacityNotConnectedError(msg)

    def _mark_disconnected(self) -> None:
        self._connected = False

    def _close_file(self, handle: TextIO | None, label: str) -> None:
        if handle is None or handle.closed:
            return
        try:
            handle.close()
        except OSError as exc:
            self._logger.warning("Error closing %s pipe: %s", label, exc)


def _summarize_response(response: str) -> str:
    """Collapse a multi-line pipe response for concise debug logging."""
    summary = response.strip().replace("\n", " | ")
    if len(summary) > 120:
        return summary[:117] + "..."
    return summary
