"""Tests for export format resolution."""

from __future__ import annotations

from vinylsplit.export.formats import resolve_export_format
from vinylsplit.metadata.session import ExportFormat


def test_resolve_export_format_accepts_enum() -> None:
    assert resolve_export_format(ExportFormat.FLAC) is ExportFormat.FLAC


def test_resolve_export_format_accepts_combo_string_value() -> None:
    assert resolve_export_format("flac") is ExportFormat.FLAC
    assert resolve_export_format("FLAC") is ExportFormat.FLAC