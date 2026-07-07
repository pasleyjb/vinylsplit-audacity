"""Reusable wizard page classes."""

from vinylsplit.wizard.pages.artist_search_page import ArtistSearchPage
from vinylsplit.wizard.pages.base import WizardPageBase
from vinylsplit.wizard.pages.finish_page import FinishPage
from vinylsplit.wizard.pages.label_placement_page import LabelPlacementPage
from vinylsplit.wizard.pages.release_selection_page import ReleaseSelectionPage
from vinylsplit.wizard.pages.review_page import ReviewPage
from vinylsplit.wizard.pages.track_list_page import TrackListPage
from vinylsplit.wizard.pages.welcome_page import WelcomePage

__all__ = [
    "ArtistSearchPage",
    "FinishPage",
    "LabelPlacementPage",
    "ReleaseSelectionPage",
    "ReviewPage",
    "TrackListPage",
    "WelcomePage",
    "WizardPageBase",
]
