#!/usr/bin/env python3
"""Development utility: fetch Audacity command help and save as Markdown.

Requires Audacity to be running with mod-script-pipe enabled.

The utility discovers command names via Brief-format listing, queries each
command individually through ``Help``, and merges the results into a single
reference document.

Usage::

    python scratch/list_commands.py

Output is written to ``docs/audacity_commands.md``.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

# Allow running without installing the package.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from vinylsplit.audacity.client import (  # noqa: E402
    AudacityClient,
    AudacityClientConfig,
    AudacityCommandError,
    AudacityError,
)
from vinylsplit.core.logging_config import configure_logging  # noqa: E402

OUTPUT_PATH = PROJECT_ROOT / "docs" / "audacity_commands.md"

_BATCH_PREFIX = re.compile(r"^BatchCommand of \d+ command\(s\) returned:\s*$")
_BATCH_TRAILER = re.compile(r"^BatchCommand finished:.*$")


@dataclass
class CommandBrief:
    """Brief-format metadata for a single Audacity command."""

    command_id: str
    display_name: str
    url: str
    description: str


@dataclass
class CommandHelp:
    """Merged help payload for one Audacity command."""

    command_id: str
    brief: CommandBrief | None = None
    detail: dict[str, object] | None = None
    error: str | None = None


@dataclass
class CommandCatalog:
    """Full catalog assembled from multiple Audacity queries."""

    discovered_via: str
    commands: list[CommandHelp] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)


def extract_help_body(response: str) -> str:
    """Strip mod-script-pipe batch framing from a Help response."""
    lines: list[str] = []
    for line in response.splitlines():
        if _BATCH_PREFIX.match(line) or _BATCH_TRAILER.match(line):
            continue
        lines.append(line.rstrip())

    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    return "\n".join(lines)


def parse_quoted_fields(text: str) -> list[str]:
    """Parse Brief-format quoted fields, honoring backslash-escaped quotes."""
    fields: list[str] = []
    index = 0
    length = len(text)

    while index < length:
        if text[index] != '"':
            index += 1
            continue

        index += 1
        chars: list[str] = []
        while index < length:
            char = text[index]
            if char == "\\" and index + 1 < length:
                chars.append(text[index + 1])
                index += 2
                continue
            if char == '"':
                index += 1
                break
            chars.append(char)
            index += 1

        fields.append("".join(chars))

    return fields


def parse_brief_line(line: str) -> CommandBrief | None:
    """Parse one Brief-format command line into structured metadata."""
    stripped = line.strip()
    if not stripped or stripped == "Command not found":
        return None

    fields = parse_quoted_fields(stripped)
    if len(fields) < 4:
        return None

    return CommandBrief(
        command_id=fields[0],
        display_name=fields[1],
        url=fields[2],
        description=fields[3],
    )


def discover_command_names(client: AudacityClient) -> tuple[list[str], str]:
    """Discover command IDs using Brief-format responses.

    Audacity's bare ``Help: Format=Brief`` only documents the Help command
    itself. The full catalog is exposed through
    ``GetInfo: Type=Commands Format=Brief``, which returns one Brief line per
    command.
    """
    help_brief = extract_help_body(client.execute("Help: Format=Brief"))
    help_names = _parse_brief_names(help_brief)

    catalog_brief = extract_help_body(
        client.execute("GetInfo: Type=Commands Format=Brief")
    )
    catalog_names = _parse_brief_names(catalog_brief)

    if len(catalog_names) > len(help_names):
        return catalog_names, "GetInfo: Type=Commands Format=Brief"

    if help_names:
        return help_names, "Help: Format=Brief"

    msg = "No commands discovered from Audacity Brief help output."
    raise AudacityError(msg)


def _parse_brief_names(brief_text: str) -> list[str]:
    """Extract command IDs from Brief-format text."""
    names: list[str] = []
    for line in brief_text.splitlines():
        brief = parse_brief_line(line)
        if brief is not None:
            names.append(brief.command_id)
    return names


def fetch_command_help(client: AudacityClient, command_id: str) -> CommandHelp:
    """Query Brief and JSON help for a single command."""
    entry = CommandHelp(command_id=command_id)

    brief_response = extract_help_body(
        client.execute(f"Help: Command={command_id} Format=Brief")
    )
    if brief_response.strip() == "Command not found":
        entry.error = "Command not found"
        return entry

    entry.brief = parse_brief_line(brief_response)

    detail_response = extract_help_body(
        client.execute(f"Help: Command={command_id} Format=JSON")
    )
    if detail_response.strip() == "Command not found":
        entry.error = "Command not found"
        return entry

    try:
        parsed = json.loads(detail_response)
    except json.JSONDecodeError as exc:
        entry.error = f"Invalid JSON help response: {exc}"
        return entry

    if isinstance(parsed, dict):
        entry.detail = parsed
    else:
        entry.error = "Help response was not a JSON object."

    return entry


def build_catalog(client: AudacityClient) -> CommandCatalog:
    """Discover commands and query help for each one."""
    command_ids, discovered_via = discover_command_names(client)
    catalog = CommandCatalog(discovered_via=discovered_via)

    total = len(command_ids)
    print(f"Discovered {total} commands via {discovered_via}")

    for index, command_id in enumerate(command_ids, start=1):
        print(f"Querying {index}/{total}: {command_id}")
        try:
            entry = fetch_command_help(client, command_id)
        except AudacityCommandError as exc:
            catalog.failed.append(command_id)
            catalog.commands.append(CommandHelp(command_id=command_id, error=str(exc)))
            continue

        if entry.error:
            catalog.failed.append(command_id)
        catalog.commands.append(entry)

    return catalog


def format_as_markdown(catalog: CommandCatalog) -> str:
    """Render the merged command catalog as Markdown."""
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    successful = [cmd for cmd in catalog.commands if not cmd.error]

    sections: list[str] = [
        "# Audacity mod-script-pipe Commands",
        "",
        (
            "> Auto-generated reference from Audacity Help output. "
            "Re-run `python scratch/list_commands.py` to refresh."
        ),
        "",
        f"**Generated:** {generated_at}  ",
        "**Source:** `scratch/list_commands.py`  ",
        f"**Discovery query:** `{catalog.discovered_via}`  ",
        f"**Total commands:** {len(catalog.commands)}  ",
        f"**Successful lookups:** {len(successful)}  ",
        f"**Failed lookups:** {len(catalog.failed)}",
        "",
        "## Overview",
        "",
        (
            "This document merges Brief-format command discovery with per-command "
            "`Help` queries. Each command section includes Brief metadata and the "
            "full JSON schema returned by Audacity."
        ),
        "",
        "## Command Index",
        "",
    ]

    sections.extend(_format_index_table(catalog.commands))
    sections.append("")
    sections.append("## Commands")
    sections.append("")

    for entry in catalog.commands:
        sections.extend(_format_command_section(entry))
        sections.append("")

    if catalog.failed:
        sections.extend(
            [
                "## Failed Lookups",
                "",
                "The following commands could not be resolved via `Help`:",
                "",
            ]
        )
        for command_id in catalog.failed:
            sections.append(f"- `{command_id}`")
        sections.append("")

    return "\n".join(sections)


def _format_index_table(commands: list[CommandHelp]) -> list[str]:
    """Render the summary index table."""
    rows: list[str] = [
        "| Command | Name | Description |",
        "| --- | --- | --- |",
    ]

    for entry in commands:
        name = ""
        description = ""

        if entry.detail is not None:
            name = str(entry.detail.get("name", ""))
            description = str(entry.detail.get("tip", ""))
        if entry.brief is not None:
            if not name:
                name = entry.brief.display_name
            if not description:
                description = entry.brief.description
        if not name and not description:
            description = entry.error or ""

        safe_name = name.replace("|", "\\|")
        safe_description = description.replace("|", "\\|").replace("\n", " ")
        status = "" if not entry.error else f" _(error: {entry.error})_"
        rows.append(
            f"| `{entry.command_id}` | {safe_name} | {safe_description}{status} |"
        )

    return rows


def _format_command_section(entry: CommandHelp) -> list[str]:
    """Render one command section."""
    lines = [f"### {entry.command_id}", ""]

    if entry.error:
        lines.append(f"_Help lookup failed: {entry.error}_")
        lines.append("")
        return lines

    if entry.brief is not None:
        lines.extend(
            [
                f"**Name:** {entry.brief.display_name}  ",
                f"**Manual URL:** {entry.brief.url}  ",
                f"**Description:** {entry.brief.description}",
                "",
            ]
        )

    if entry.detail is not None:
        lines.append("**JSON Schema:**")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(entry.detail, indent=2, sort_keys=True))
        lines.append("```")

    return lines


def main() -> int:
    """Connect to Audacity, query all commands, and write Markdown output."""
    configure_logging(log_to_file=False)

    config = AudacityClientConfig(read_timeout=30.0)
    client = AudacityClient(config=config)

    print("Connecting to Audacity...")
    try:
        client.connect()
        catalog = build_catalog(client)
    except AudacityError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        client.disconnect()

    markdown = format_as_markdown(catalog)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(markdown, encoding="utf-8")

    print(f"Wrote {OUTPUT_PATH}")
    if catalog.failed:
        print(f"Warning: {len(catalog.failed)} command(s) failed lookup.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
