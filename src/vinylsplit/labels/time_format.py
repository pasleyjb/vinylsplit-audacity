"""Human-readable timeline formatting for label regions."""

from __future__ import annotations


def format_position(seconds: float) -> str:
    """Format a timeline position as ``MM:SS`` or ``HH:MM:SS``."""
    total = max(int(seconds), 0)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_difference_seconds(difference: float) -> str:
    """Format a signed position delta as ``+MM:SS`` or ``-MM:SS``."""
    sign = "+" if difference >= 0 else "-"
    total = abs(int(difference))
    minutes, secs = divmod(total, 60)
    return f"{sign}{minutes:02d}:{secs:02d}"


def format_region_range(start_seconds: float, end_seconds: float) -> str:
    """Format a region span as ``start → end``."""
    return f"{format_position(start_seconds)} → {format_position(end_seconds)}"