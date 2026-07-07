"""Reusable wizard page classes."""

from vinylsplit.wizard.pages.artist_search_page import ArtistSearchPage
from vinylsplit.wizard.pages.base import WizardPageBase
from vinylsplit.wizard.pages.finish_page import FinishPage
from vinylsplit.wizard.pages.generate_album_layout_page import GenerateAlbumLayoutPage
from vinylsplit.wizard.pages.release_selection_page import ReleaseSelectionPage
from vinylsplit.wizard.pages.review_page import ReviewPage
from vinylsplit.wizard.pages.track_list_page import TrackListPage
from vinylsplit.wizard.pages.welcome_page import WelcomePage

__all__ = [
    "ArtistSearchPage",
    "FinishPage",
    "GenerateAlbumLayoutPage",
    "ReleaseSelectionPage",
    "ReviewPage",
    "TrackListPage",
    "WelcomePage",
    "WizardPageBase",
]