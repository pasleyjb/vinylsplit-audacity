"""Tests for wizard styling helpers."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette

from vinylsplit.wizard.ui_style import build_wizard_stylesheet


def _palette_with_window_color(hex_color: str) -> QPalette:
    palette = QPalette()
    color = QColor(hex_color)
    palette.setColor(QPalette.ColorRole.Window, color)
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff" if color.lightness() < 128 else "#111111"))
    palette.setColor(QPalette.ColorRole.Base, color)
    palette.setColor(QPalette.ColorRole.AlternateBase, color.darker(110))
    palette.setColor(QPalette.ColorRole.Button, color)
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#ffffff" if color.lightness() < 128 else "#111111"))
    palette.setColor(QPalette.ColorRole.Mid, color.darker(130))
    return palette


def test_build_wizard_stylesheet_uses_palette_window_color() -> None:
    light = build_wizard_stylesheet(_palette_with_window_color("#f4f5f7"))
    dark = build_wizard_stylesheet(_palette_with_window_color("#1e1e1e"))

    assert "background-color: #f4f5f7;" in light
    assert "background-color: #1e1e1e;" in dark
    assert "#eef2ff" in light
    assert "#1e293b" in dark