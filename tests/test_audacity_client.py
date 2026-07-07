"""Tests for :class:`vinylsplit.audacity.client.AudacityClient`."""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import TextIO
from unittest.mock import patch

import pytest

from vinylsplit.audacity.client import (
    AudacityClient,
    AudacityClientConfig,
    AudacityCommandError,
    AudacityConnectionError,
    AudacityNotConnectedError,
    AudacityPipeBrokenError,
    AudacityTimeoutError,
    PipePaths,
    detect_pipe_paths,
)


@pytest.fixture
def pipe_paths(tmp_path: Path) -> PipePaths:
    """Provide writable pipe path placeholders."""
    to_pipe = tmp_path / "audacity_script_pipe.to.1000"
    from_pipe = tmp_path / "audacity_script_pipe.from.1000"
    to_pipe.touch()
    from_pipe.touch()
    return PipePaths(to_pipe=to_pipe, from_pipe=from_pipe)


@pytest.fixture
def client(pipe_paths: PipePaths) -> AudacityClient:
    """Provide a client with explicit pipe paths and fast timeouts."""
    config = AudacityClientConfig(
        connect_timeout=1.0,
        read_timeout=1.0,
        pipe_paths=pipe_paths,
    )
    return AudacityClient(config=config)


def _make_opener(
    to_buffer: io.StringIO | None = None,
    from_buffer: io.StringIO | None = None,
):
    """Return an opener that yields in-memory streams instead of real FIFOs."""

    def opener(path: Path, mode: str, **kwargs: object) -> TextIO:
        if "w" in mode:
            return to_buffer or io.StringIO()
        return from_buffer or io.StringIO()

    return opener


def test_detect_pipe_paths_linux() -> None:
    with patch.object(os, "getuid", return_value=1000):
        paths = detect_pipe_paths()

    assert paths.to_pipe == Path("/tmp/audacity_script_pipe.to.1000")
    assert paths.from_pipe == Path("/tmp/audacity_script_pipe.from.1000")


def test_connect_raises_when_pipes_missing(tmp_path: Path) -> None:
    config = AudacityClientConfig(
        pipe_paths=PipePaths(
            to_pipe=tmp_path / "missing.to",
            from_pipe=tmp_path / "missing.from",
        )
    )
    client = AudacityClient(config=config)

    with pytest.raises(AudacityConnectionError, match="not available"):
        client.connect()


def test_connect_and_disconnect(client: AudacityClient) -> None:
    client.opener = _make_opener()
    client.connect()

    assert client.is_connected()

    client.disconnect()
    assert not client.is_connected()


def test_connect_is_idempotent(client: AudacityClient) -> None:
    client.opener = _make_opener()
    client.connect()
    client.connect()
    assert client.is_connected()


def test_send_command_requires_connection(client: AudacityClient) -> None:
    with pytest.raises(AudacityNotConnectedError):
        client.send_command("Help:")


def test_send_command_appends_newline(client: AudacityClient) -> None:
    to_buffer = io.StringIO()
    client.opener = _make_opener(to_buffer=to_buffer)
    client.connect()

    client.send_command("Help:")

    assert to_buffer.getvalue() == "Help:\n"


def test_read_response_returns_complete_block(client: AudacityClient) -> None:
    response_body = (
        "BatchCommand of 1 command(s) returned:\n"
        "Help: ...\n"
        "BatchCommand finished: OK!\n"
        "\n"
    )
    from_buffer = io.StringIO(response_body)
    client.opener = _make_opener(from_buffer=from_buffer)
    client.connect()

    result = client.read_response()

    assert "BatchCommand finished: OK!" in result
    assert result.endswith("BatchCommand finished: OK!\n")


def test_read_response_raises_on_eof(client: AudacityClient) -> None:
    client.opener = _make_opener(from_buffer=io.StringIO(""))
    client.connect()

    with pytest.raises(AudacityPipeBrokenError, match="closed before"):
        client.read_response()


def test_read_response_raises_on_timeout(client: AudacityClient) -> None:
    blocking = io.StringIO()
    blocking.readline = lambda: (_ for _ in ()).throw(BlockingIOError)  # type: ignore[method-assign]

    client.opener = _make_opener(from_buffer=blocking)
    client.connect()

    with (
        patch.object(
            client,
            "_readline_with_timeout",
            side_effect=AudacityTimeoutError("timeout"),
        ),
        pytest.raises(AudacityTimeoutError),
    ):
        client.read_response()


def test_execute_validates_success(client: AudacityClient) -> None:
    to_buffer = io.StringIO()
    from_buffer = io.StringIO(
        "BatchCommand of 1 command(s) returned:\n"
        "OK\n"
        "BatchCommand finished: OK!\n"
        "\n"
    )
    client.opener = _make_opener(to_buffer=to_buffer, from_buffer=from_buffer)
    client.connect()

    response = client.execute("Help:")

    assert "BatchCommand finished: OK!" in response
    assert to_buffer.getvalue() == "Help:\n"


def test_execute_raises_on_failed_batch(client: AudacityClient) -> None:
    from_buffer = io.StringIO(
        "BatchCommand of 1 command(s) returned:\n"
        "Error\n"
        "BatchCommand finished: Failed!\n"
        "\n"
    )
    client.opener = _make_opener(from_buffer=from_buffer)
    client.connect()

    with pytest.raises(AudacityCommandError) as exc_info:
        client.execute("BadCommand:")

    assert "BatchCommand finished: Failed" in exc_info.value.response


def test_help_default_sends_general_help(client: AudacityClient) -> None:
    to_buffer = io.StringIO()
    from_buffer = io.StringIO("BatchCommand finished: OK!\n\n")
    client.opener = _make_opener(to_buffer=to_buffer, from_buffer=from_buffer)
    client.connect()

    client.help()

    assert to_buffer.getvalue() == "Help:\n"


def test_help_specific_command(client: AudacityClient) -> None:
    to_buffer = io.StringIO()
    from_buffer = io.StringIO("BatchCommand finished: OK!\n\n")
    client.opener = _make_opener(to_buffer=to_buffer, from_buffer=from_buffer)
    client.connect()

    client.help("GetInfo")

    assert to_buffer.getvalue() == 'Help: Command="GetInfo"\n'


def test_send_command_handles_broken_pipe(client: AudacityClient) -> None:
    to_buffer = io.StringIO()

    def broken_write(_: str) -> int:
        msg = "broken"
        raise BrokenPipeError(msg)

    to_buffer.write = broken_write  # type: ignore[method-assign]

    client.opener = _make_opener(to_buffer=to_buffer, from_buffer=io.StringIO("\n\n"))
    client.connect()

    with pytest.raises(AudacityPipeBrokenError):
        client.send_command("Help:")

    assert not client.is_connected()


def test_open_timeout_raises(client: AudacityClient) -> None:
    def slow_opener(path: Path, mode: str, **kwargs: object) -> TextIO:
        import time

        time.sleep(2)
        return io.StringIO()

    client.opener = slow_opener
    client.config.connect_timeout = 0.1

    with pytest.raises(AudacityTimeoutError, match="Timed out"):
        client.connect()
