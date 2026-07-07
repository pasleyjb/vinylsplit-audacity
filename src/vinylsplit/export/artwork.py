"""Album artwork retrieval from the Cover Art Archive."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from vinylsplit import __version__
from vinylsplit.metadata.session import AlbumArtwork

_logger = logging.getLogger(__name__)

_COVER_ART_ARCHIVE_BASE = "https://coverartarchive.org"
_USER_AGENT = (
    f"vinylsplit-audacity/{__version__} "
    "(https://github.com/vinylsplit/vinylsplit-audacity)"
)


@dataclass(frozen=True)
class ArtworkFetchResult:
    """Outcome of a cover art lookup."""

    artwork: AlbumArtwork | None
    message: str


def fetch_release_artwork(
    release_id: str,
    *,
    session: requests.Session | None = None,
    timeout: float = 15.0,
) -> ArtworkFetchResult:
    """Download front cover art for a MusicBrainz release."""
    release_id = release_id.strip()
    if not release_id:
        return ArtworkFetchResult(None, "Release id is required for artwork lookup.")

    http = session or requests.Session()
    metadata_url = f"{_COVER_ART_ARCHIVE_BASE}/release/{release_id}"
    headers = {"User-Agent": _USER_AGENT}

    try:
        response = http.get(metadata_url, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        _logger.warning("Cover art metadata request failed: %s", exc)
        return ArtworkFetchResult(None, f"Could not reach Cover Art Archive: {exc}")

    if response.status_code == 404:
        return ArtworkFetchResult(None, "No cover art is available for this release.")

    if response.status_code != 200:
        return ArtworkFetchResult(
            None,
            f"Cover Art Archive returned HTTP {response.status_code}.",
        )

    try:
        payload = response.json()
    except ValueError:
        return ArtworkFetchResult(None, "Cover Art Archive returned invalid JSON.")

    image = _select_front_image(payload)
    if image is None:
        return ArtworkFetchResult(None, "No front cover image was found.")

    image_url = image.get("image")
    if not isinstance(image_url, str) or not image_url:
        return ArtworkFetchResult(None, "Cover art image URL is missing.")

    try:
        image_response = http.get(image_url, headers=headers, timeout=timeout)
        image_response.raise_for_status()
    except requests.RequestException as exc:
        _logger.warning("Cover art download failed: %s", exc)
        return ArtworkFetchResult(None, f"Could not download cover art: {exc}")

    mime_type = image_response.headers.get("Content-Type", "image/jpeg")
    if ";" in mime_type:
        mime_type = mime_type.split(";", 1)[0].strip()

    artwork = AlbumArtwork(
        data=image_response.content,
        mime_type=mime_type,
        source_url=image_url,
    )
    return ArtworkFetchResult(artwork, "Album artwork loaded.")


def _select_front_image(payload: object) -> dict[str, object] | None:
    if not isinstance(payload, dict):
        return None

    images = payload.get("images")
    if not isinstance(images, list):
        return None

    front_images = [
        image
        for image in images
        if isinstance(image, dict) and image.get("front") is True
    ]
    if front_images:
        return front_images[0]

    for image in images:
        if isinstance(image, dict):
            return image

    return None