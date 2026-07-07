"""Album artwork retrieval from the Cover Art Archive."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

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


_MIME_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def artwork_file_extension(mime_type: str | None) -> str:
    """Return a file extension for cover art based on its MIME type."""
    if mime_type:
        extension = _MIME_EXTENSIONS.get(mime_type.lower())
        if extension is not None:
            return extension
    return ".jpg"


def write_album_folder_artwork(
    directory: Path,
    artwork: AlbumArtwork,
) -> Path | None:
    """Write cover art into an album folder for display and folder thumbnails."""
    if not artwork.is_available or not artwork.data:
        return None

    directory.mkdir(parents=True, exist_ok=True)
    cover_path = directory / f"cover{artwork_file_extension(artwork.mime_type)}"
    cover_path.write_bytes(artwork.data)

    if cover_path.suffix.lower() in {".jpg", ".jpeg"}:
        folder_path = directory / "folder.jpg"
        if folder_path != cover_path:
            folder_path.write_bytes(artwork.data)

    directory_file = directory / ".directory"
    directory_file.write_text(
        "[Desktop Entry]\n"
        f"Icon={cover_path.name}\n"
        "Type=Directory\n",
        encoding="utf-8",
    )
    return cover_path


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