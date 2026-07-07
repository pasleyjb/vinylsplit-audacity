"""Generate the VinylSplit application icon for Linux packaging."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QGuiApplication


def generate_icon(path: Path, *, size: int = 256) -> None:
    """Render a simple branded icon to *path*."""
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(QColor("#4f46e5"))

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor("#ffffff"))
    font = QFont()
    font.setBold(True)
    font.setPixelSize(size // 3)
    painter.setFont(font)
    painter.drawText(image.rect(), Qt.AlignmentFlag.AlignCenter, "VS")
    painter.end()

    path.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(path)):
        msg = f"Could not write icon to {path}"
        raise OSError(msg)


if __name__ == "__main__":
    app = QGuiApplication([])
    generate_icon(Path(__file__).with_name("vinylsplit.png"))
    app.quit()