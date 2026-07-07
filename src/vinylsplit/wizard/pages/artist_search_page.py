"""Artist and album search wizard page."""

from __future__ import annotations

from typing import ClassVar

from PySide6.QtWidgets import QFormLayout, QLineEdit

from vinylsplit.wizard.pages.base import WizardPageBase
from vinylsplit.wizard.pages.page_ids import PageId


class ArtistSearchPage(WizardPageBase):
    """Collect artist and album search terms for MusicBrainz lookup."""

    PAGE_ID: ClassVar[int] = PageId.ARTIST_SEARCH
    PAGE_TITLE: ClassVar[str] = "Artist & Album Search"
    PAGE_SUBTITLE: ClassVar[str] = "Enter the artist and album you are digitizing."

    def build_content(self) -> None:
        form = QFormLayout()
        self.artist_input = QLineEdit()
        self.artist_input.setPlaceholderText("e.g. Pink Floyd")
        self.album_input = QLineEdit()
        self.album_input.setPlaceholderText("e.g. The Dark Side of the Moon")

        form.addRow("Artist:", self.artist_input)
        form.addRow("Album:", self.album_input)
        self._layout.addLayout(form)

        self._layout.addWidget(
            self._create_placeholder_label(
                "MusicBrainz search is not yet implemented. "
                "Inputs are preserved for future integration."
            )
        )

        # Restore last-used values from settings when available.
        settings = self.container.settings
        last_artist = settings.get(settings.KEY_LAST_ARTIST, "")
        last_album = settings.get(settings.KEY_LAST_ALBUM, "")
        if last_artist:
            self.artist_input.setText(str(last_artist))
        if last_album:
            self.album_input.setText(str(last_album))

    def cleanupPage(self) -> None:
        settings = self.container.settings
        settings.set(settings.KEY_LAST_ARTIST, self.artist_input.text().strip())
        settings.set(settings.KEY_LAST_ALBUM, self.album_input.text().strip())
        settings.sync()
        super().cleanupPage()
