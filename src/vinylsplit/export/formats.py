"""Export format helpers."""

from __future__ import annotations

from vinylsplit.metadata.session import ExportFormat


def resolve_export_format(value: object) -> ExportFormat | None:
    """Resolve a combo-box or session value to :class:`ExportFormat`.

    PySide6 stores ``StrEnum`` user data as plain strings, so callers must
    accept either an :class:`ExportFormat` instance or its ``.value`` string.
    """
    if isinstance(value, ExportFormat):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        try:
            return ExportFormat(normalized)
        except ValueError:
            return None
    return None