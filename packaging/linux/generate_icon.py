"""Ensure the VinylSplit application icon exists for Linux packaging.

Prefers the designed brand icon under ``assets/`` / ``resources/icons/``.
Only falls back to a generated placeholder if no brand asset is present.
"""

from __future__ import annotations

import shutil
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def ensure_icon(path: Path, *, size: int = 256) -> None:
    """Copy or generate the application icon at *path*."""
    root = _project_root()
    preferred = [
        root / "assets" / f"vinylsplit-{size}.png",
        root / "assets" / "vinylsplit.png",
        root / "assets" / "vinylsplit-icon-source.png",
        root / "src" / "vinylsplit" / "resources" / "icons" / "vinylsplit.png",
        root / "packaging" / "linux" / "vinylsplit.png",
    ]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    for candidate in preferred:
        if candidate.is_file() and candidate.resolve() != path.resolve():
            shutil.copyfile(candidate, path)
            return
        if candidate.is_file() and candidate.resolve() == path.resolve():
            return

    # Last resort placeholder
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter

    app = QGuiApplication.instance() or QGuiApplication([])
    del app
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(QColor("#e11d2e"))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor("#ffffff"))
    font = QFont()
    font.setBold(True)
    font.setPixelSize(size // 3)
    painter.setFont(font)
    painter.drawText(image.rect(), Qt.AlignmentFlag.AlignCenter, "VS")
    painter.end()
    if not image.save(str(path)):
        msg = f"Could not write icon to {path}"
        raise OSError(msg)


def generate_icon(path: Path, *, size: int = 256) -> None:
    """Compatibility wrapper used by packaging scripts."""
    ensure_icon(path, size=size)


if __name__ == "__main__":
    generate_icon(Path(__file__).with_name("vinylsplit.png"))
