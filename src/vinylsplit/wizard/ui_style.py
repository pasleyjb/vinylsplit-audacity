"""Shared styling helpers for the VinylSplit wizard."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QImage, QPalette, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

PAGE_MARGIN = 4
PAGE_SPACING = 12
TABLE_MIN_HEIGHT = 180
ARTWORK_PREVIEW_SIZE = 168


def build_wizard_stylesheet(palette: QPalette) -> str:
    """Build a wizard stylesheet that follows the active system palette."""
    window = palette.color(QPalette.ColorRole.Window).name()
    base = palette.color(QPalette.ColorRole.Base).name()
    alternate = palette.color(QPalette.ColorRole.AlternateBase).name()
    text = palette.color(QPalette.ColorRole.WindowText).name()
    button = palette.color(QPalette.ColorRole.Button).name()
    button_text = palette.color(QPalette.ColorRole.ButtonText).name()
    border = palette.color(QPalette.ColorRole.Mid).name()
    is_dark = palette.color(QPalette.ColorRole.Window).lightness() < 128

    if is_dark:
        banner_bg = "#1e293b"
        banner_border = "#475569"
        banner_text = "#e2e8f0"
        success = "#4ade80"
        error = "#f87171"
        muted = "#94a3b8"
        neutral = "#e2e8f0"
        secondary_hover = alternate
    else:
        banner_bg = "#eef2ff"
        banner_border = "#c7d2fe"
        banner_text = "#1e293b"
        success = "#166534"
        error = "#b91c1c"
        muted = "#64748b"
        neutral = "#334155"
        secondary_hover = "#f8fafc"

    return f"""
QWizard {{
    background-color: {window};
    color: {text};
}}
QWizardPage {{
    background-color: {window};
    color: {text};
}}
QLabel#InfoBanner {{
    background-color: {banner_bg};
    border: 1px solid {banner_border};
    border-radius: 8px;
    padding: 12px 14px;
    color: {banner_text};
}}
QLabel#StatusSuccess {{
    color: {success};
    font-weight: 600;
}}
QLabel#StatusError {{
    color: {error};
    font-weight: 600;
}}
QLabel#StatusMuted {{
    color: {muted};
}}
QLabel#StatusNeutral {{
    color: {neutral};
    font-weight: 600;
}}
QLabel#ArtworkPreview {{
    background-color: {base};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 8px;
    color: {text};
}}
QGroupBox {{
    font-weight: 600;
    border: 1px solid {border};
    border-radius: 8px;
    margin-top: 12px;
    padding: 14px 12px 12px 12px;
    background-color: {base};
    color: {text};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: {text};
}}
QPushButton#PrimaryButton {{
    background-color: #4f46e5;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
    font-weight: 600;
}}
QPushButton#PrimaryButton:hover {{
    background-color: #4338ca;
}}
QPushButton#PrimaryButton:disabled {{
    background-color: {"#6366f1" if is_dark else "#a5b4fc"};
}}
QPushButton#SecondaryButton {{
    background-color: {button};
    color: {button_text};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 8px 14px;
}}
QPushButton#SecondaryButton:hover {{
    background-color: {secondary_hover};
}}
QTableWidget {{
    background-color: {base};
    color: {text};
    border: 1px solid {border};
    border-radius: 6px;
    gridline-color: {border};
}}
QHeaderView::section {{
    background-color: {alternate};
    color: {text};
    padding: 6px 8px;
    border: none;
    border-bottom: 1px solid {border};
    font-weight: 600;
}}
QProgressBar {{
    border: 1px solid {border};
    border-radius: 6px;
    text-align: center;
    background-color: {base};
    color: {text};
}}
QProgressBar::chunk {{
    background-color: #4f46e5;
    border-radius: 5px;
}}
"""


def apply_wizard_theme(widget: QWidget) -> None:
    """Apply palette-aware styling and refresh when the system theme changes."""
    app = QApplication.instance()
    if app is None:
        return

    def refresh() -> None:
        widget.setStyleSheet(build_wizard_stylesheet(app.palette()))

    refresh()
    app.paletteChanged.connect(refresh)
    app.styleHints().colorSchemeChanged.connect(refresh)


def apply_page_layout(layout: QVBoxLayout) -> None:
    """Apply consistent outer margins and vertical spacing."""
    layout.setContentsMargins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
    layout.setSpacing(PAGE_SPACING)


def create_info_banner(text: str) -> QLabel:
    """Create a highlighted instruction banner."""
    label = QLabel(text)
    label.setObjectName("InfoBanner")
    label.setWordWrap(True)
    label.setTextFormat(Qt.TextFormat.RichText)
    font = QFont()
    font.setPointSize(10)
    label.setFont(font)
    return label


def create_section_group(title: str) -> QGroupBox:
    """Create a titled content group."""
    group = QGroupBox(title)
    return group


def create_status_label(*, tone: str = "muted") -> QLabel:
    """Create a status label with semantic styling."""
    label = QLabel("")
    label.setWordWrap(True)
    if tone == "success":
        label.setObjectName("StatusSuccess")
    elif tone == "error":
        label.setObjectName("StatusError")
    elif tone == "neutral":
        label.setObjectName("StatusNeutral")
    else:
        label.setObjectName("StatusMuted")
    return label


def style_primary_button(button: QPushButton, text: str) -> None:
    """Apply primary action styling."""
    button.setText(text)
    button.setObjectName("PrimaryButton")
    button.setCursor(Qt.CursorShape.PointingHandCursor)


def style_secondary_button(button: QPushButton, text: str | None = None) -> None:
    """Apply secondary action styling."""
    if text is not None:
        button.setText(text)
    button.setObjectName("SecondaryButton")
    button.setCursor(Qt.CursorShape.PointingHandCursor)


def configure_data_table(table: QTableWidget, *, min_height: int = TABLE_MIN_HEIGHT) -> None:
    """Apply consistent table presentation defaults."""
    from PySide6.QtWidgets import QHeaderView

    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    table.verticalHeader().setVisible(False)
    table.setMinimumHeight(min_height)
    header = table.horizontalHeader()
    header.setStretchLastSection(True)
    header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)


def add_layout_stretch(layout: QVBoxLayout) -> None:
    """Push content toward the top of a page."""
    layout.addStretch(1)


def artwork_preview_pixmap(data: bytes, *, max_edge: int = ARTWORK_PREVIEW_SIZE) -> QPixmap:
    """Scale cover art for the finish page preview."""
    image = QImage.fromData(data)
    if image.isNull():
        return QPixmap()
    return QPixmap.fromImage(image).scaled(
        max_edge,
        max_edge,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def build_artwork_preview_panel() -> tuple[QWidget, QLabel, QLabel]:
    """Build artwork preview widget with image and caption labels."""
    panel = QWidget()
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)

    image_label = QLabel("No artwork yet")
    image_label.setObjectName("ArtworkPreview")
    image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    image_label.setMinimumSize(ARTWORK_PREVIEW_SIZE, ARTWORK_PREVIEW_SIZE)
    image_label.setMaximumSize(ARTWORK_PREVIEW_SIZE, ARTWORK_PREVIEW_SIZE)

    caption_label = create_status_label(tone="muted")
    caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    layout.addWidget(image_label)
    layout.addWidget(caption_label)
    return panel, image_label, caption_label


def connection_status_text(*, connected: bool) -> str:
    """Return user-facing Audacity connection status text."""
    return "Connected to Audacity" if connected else "Not connected to Audacity"


def finish_button_label(*, export_completed: bool) -> str:
    """Return the appropriate Finish button caption."""
    return "Close" if export_completed else "Export && Finish"