"""Tests for linear wizard page navigation."""

from __future__ import annotations

from vinylsplit.app import create_wizard
from vinylsplit.wizard.pages.page_ids import PageId


def test_linear_next_ids(container) -> None:
    wizard = create_wizard(container)
    flow = [
        PageId.OPEN,
        PageId.RELEASE,
        PageId.ALIGN,
        PageId.EXPORT,
    ]
    for current_id, next_id in zip(flow, flow[1:], strict=False):
        page = wizard.page(current_id)
        assert page is not None
        assert page.nextId() == next_id

    assert wizard.page(PageId.EXPORT).nextId() == -1
    # Legacy pages are not registered in the streamlined wizard.
    assert wizard.page(PageId.RELEASE_SELECTION) is None
    assert wizard.page(PageId.TRACK_LIST) is None
    assert wizard.page(PageId.REVIEW) is None


def test_restart_for_new_album(container, session) -> None:
    wizard = create_wizard(container)
    session.set_audacity_connected(True)
    session.export_completed = True
    wizard.restart_for_new_album()
    assert session.export_completed is False
    assert session.audacity_connected is False
    assert wizard.currentId() == PageId.OPEN