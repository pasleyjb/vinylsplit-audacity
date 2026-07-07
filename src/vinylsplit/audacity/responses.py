"""Helpers for parsing mod-script-pipe responses."""

from __future__ import annotations

import json
import re
from typing import Any

_BATCH_TRAILER = re.compile(r"^BatchCommand finished:.*$", re.MULTILINE)


def extract_response_body(response: str) -> str:
    """Strip mod-script-pipe batch framing from a command response."""
    lines: list[str] = []
    for line in response.splitlines():
        if line.startswith("BatchCommand"):
            continue
        lines.append(line.rstrip())

    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    return "\n".join(lines)


def parse_json_response(response: str) -> Any:
    """Parse JSON embedded in a pipe response."""
    body = extract_response_body(response)
    if not body:
        msg = "Audacity returned an empty response body."
        raise ValueError(msg)
    return json.loads(body)
