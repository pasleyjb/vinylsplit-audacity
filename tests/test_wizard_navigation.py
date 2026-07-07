"""Tests for linear wizard page navigation."""

from __future__ import annotations

from vinylsplit.app import create_wizard
from vinylsplit.wizard.pages.page_ids import PageId


def test_linear_next_ids(container) -> None:
    wizard = create_wizard(container)
    flow = [
        PageId.WELCOME,
        PageId.ARTIST_SEARCH,
        PageId.RELEASE_SELECTION,
        PageId.TRACK_LIST,
        PageId.GENERATE_ALBUM_LAYOUT,
        PageId.REVIEW,
        PageId.FINISH,
    ]
    for current_id, next_id in zip(flow, flow[1:], strict=False):
        page = wizard.page(current_id)
        assert page.nextId() == next_id

    assert wizard.page(PageId.FINISH).nextId() == -1