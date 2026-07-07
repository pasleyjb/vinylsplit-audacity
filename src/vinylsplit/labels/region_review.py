"""Compare expected and current Audacity region layouts."""

from __future__ import annotations

from dataclasses import dataclass

from vinylsplit.labels.layout_engine import AlbumLayout
from vinylsplit.labels.time_format import (
    format_difference_seconds,
    format_position,
    format_region_range,
)

WARNING_THRESHOLD_SECONDS = 2.0


@dataclass(frozen=True)
class RegionReviewRow:
    """One row in the Review Album Layout comparison table."""

    track_number: str
    title: str
    expected_start_seconds: float
    expected_end_seconds: float
    actual_start_seconds: float | None
    actual_end_seconds: float | None
    start_difference_seconds: float | None
    end_difference_seconds: float | None
    has_warning: bool

    @property
    def expected_display(self) -> str:
        return format_region_range(
            self.expected_start_seconds,
            self.expected_end_seconds,
        )

    @property
    def actual_display(self) -> str:
        if self.actual_start_seconds is None or self.actual_end_seconds is None:
            return "—"
        return format_region_range(
            self.actual_start_seconds,
            self.actual_end_seconds,
        )

    @property
    def difference_display(self) -> str:
        parts: list[str] = []
        if self.start_difference_seconds is not None:
            parts.append(f"start {format_difference_seconds(self.start_difference_seconds)}")
        if self.end_difference_seconds is not None:
            parts.append(f"end {format_difference_seconds(self.end_difference_seconds)}")
        if not parts:
            return "—"
        return ", ".join(parts)

    @property
    def expected_start_display(self) -> str:
        return format_position(self.expected_start_seconds)

    @property
    def expected_end_display(self) -> str:
        return format_position(self.expected_end_seconds)

    @property
    def actual_start_display(self) -> str:
        if self.actual_start_seconds is None:
            return "—"
        return format_position(self.actual_start_seconds)

    @property
    def actual_end_display(self) -> str:
        if self.actual_end_seconds is None:
            return "—"
        return format_position(self.actual_end_seconds)


def build_region_review_rows(
    layout: AlbumLayout,
    audacity_regions: list[dict[str, object]],
) -> list[RegionReviewRow]:
    """Build review rows by matching numbered region text to Audacity labels."""
    regions_by_text = _regions_indexed_by_text(audacity_regions)
    rows: list[RegionReviewRow] = []

    for region in layout.regions:
        matched = regions_by_text.get(region.label_text)
        actual_start = _region_boundary_seconds(matched, "start")
        actual_end = _region_boundary_seconds(matched, "end")
        start_difference = None
        end_difference = None
        has_warning = False

        if actual_start is not None:
            start_difference = actual_start - region.start_seconds
            if abs(start_difference) > WARNING_THRESHOLD_SECONDS:
                has_warning = True
        if actual_end is not None:
            end_difference = actual_end - region.end_seconds
            if abs(end_difference) > WARNING_THRESHOLD_SECONDS:
                has_warning = True

        rows.append(
            RegionReviewRow(
                track_number=region.track_number,
                title=region.title,
                expected_start_seconds=region.start_seconds,
                expected_end_seconds=region.end_seconds,
                actual_start_seconds=actual_start,
                actual_end_seconds=actual_end,
                start_difference_seconds=start_difference,
                end_difference_seconds=end_difference,
                has_warning=has_warning,
            )
        )

    return rows


def _regions_indexed_by_text(
    regions: list[dict[str, object]],
) -> dict[str, dict[str, object]]:
    indexed: dict[str, dict[str, object]] = {}
    for region in regions:
        text = region.get("text")
        if isinstance(text, str) and text:
            indexed[text] = region
    return indexed


def _region_boundary_seconds(
    region: dict[str, object] | None,
    key: str,
) -> float | None:
    if region is None:
        return None
    value = region.get(key)
    if isinstance(value, (int, float)):
        return float(value)
    return None