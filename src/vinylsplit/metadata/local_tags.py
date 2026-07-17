"""Read artist/album (and related) tags from a local audio file."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from mutagen import File as MutagenFile
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
from mutagen.wave import WAVE

_logger = logging.getLogger(__name__)

# Common vinyl capture / rip extensions the UI should offer.
AUDIO_FILE_FILTER = (
    "Audio files (*.wav *.flac *.mp3 *.ogg *.oga *.m4a *.aac *.aiff *.aif *.wma);;"
    "All files (*)"
)

_SUPPORTED_SUFFIXES = {
    ".wav",
    ".flac",
    ".mp3",
    ".ogg",
    ".oga",
    ".m4a",
    ".aac",
    ".aiff",
    ".aif",
    ".wma",
}

_FILENAME_ARTIST_ALBUM = re.compile(
    r"^\s*(?P<artist>.+?)\s*[-–—]\s*(?P<album>.+?)\s*$"
)


@dataclass(frozen=True)
class LocalAudioTags:
    """Tags (and fallbacks) extracted from a source audio file."""

    path: Path
    artist: str = ""
    album: str = ""
    title: str = ""
    album_artist: str = ""
    year: str = ""
    musicbrainz_album_id: str = ""
    musicbrainz_artist_id: str = ""
    source: str = "none"  # tags | filename | none

    @property
    def search_artist(self) -> str:
        """Best artist string for MusicBrainz search."""
        return (self.album_artist or self.artist).strip()

    @property
    def search_album(self) -> str:
        """Best album string for MusicBrainz search."""
        return self.album.strip()

    @property
    def has_search_seed(self) -> bool:
        """Return True when artist and/or album can seed a search."""
        return bool(self.search_artist or self.search_album)

    def summary_line(self) -> str:
        """Short human-readable summary for the UI."""
        artist = self.search_artist or "Unknown artist"
        album = self.search_album or "Unknown album"
        return f"{artist} — {album}"


def is_supported_audio_path(path: Path) -> bool:
    """Return True when *path* looks like a supported audio file."""
    return path.suffix.lower() in _SUPPORTED_SUFFIXES


def read_local_audio_tags(path: Path | str) -> LocalAudioTags:
    """Read tags from *path*, falling back to filename heuristics.

    Args:
        path: Absolute or relative path to an audio file.

    Returns:
        :class:`LocalAudioTags` with whatever artist/album data could be found.
    """
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        msg = f"Audio file not found: {resolved}"
        raise FileNotFoundError(msg)

    tags = _read_mutagen_tags(resolved)
    if tags.has_search_seed:
        return tags

    # Fall back to "Artist - Album" style filenames when tags are empty
    # (common for raw vinyl captures named after the record).
    from_name = _tags_from_filename(resolved)
    if from_name.has_search_seed:
        _logger.info("Using filename heuristics for tags: %s", resolved.name)
        return from_name

    return LocalAudioTags(path=resolved, source="none")


def _read_mutagen_tags(path: Path) -> LocalAudioTags:
    """Extract tags via mutagen; return empty strings when missing."""
    try:
        artist, album, title, album_artist, year = _extract_common_fields(path)
        mb_album, mb_artist = _extract_musicbrainz_ids(path)
    except Exception as exc:  # noqa: BLE001 — corrupt tags should not crash UI
        _logger.warning("Failed to read tags from %s: %s", path, exc)
        return LocalAudioTags(path=path, source="none")

    source = "tags" if (artist or album or album_artist or title) else "none"
    return LocalAudioTags(
        path=path,
        artist=artist,
        album=album,
        title=title,
        album_artist=album_artist,
        year=year,
        musicbrainz_album_id=mb_album,
        musicbrainz_artist_id=mb_artist,
        source=source,
    )


def _extract_common_fields(path: Path) -> tuple[str, str, str, str, str]:
    """Return artist, album, title, album_artist, year."""
    suffix = path.suffix.lower()

    if suffix == ".mp3":
        return _from_easy_id3(path)
    if suffix == ".flac":
        return _from_vorbis_like(FLAC(path))
    if suffix in {".ogg", ".oga"}:
        return _from_vorbis_like(OggVorbis(path))
    if suffix == ".wav":
        return _from_wave(path)

    # Generic path for m4a/aac/aiff/etc.
    audio = MutagenFile(path, easy=True)
    if audio is None:
        return "", "", "", "", ""
    return (
        _first(audio, "artist"),
        _first(audio, "album"),
        _first(audio, "title"),
        _first(audio, "albumartist", "album artist"),
        _first_year(audio),
    )


def _from_easy_id3(path: Path) -> tuple[str, str, str, str, str]:
    try:
        tags = EasyID3(path)
    except Exception:  # noqa: BLE001
        audio = MP3(path, ID3=EasyID3)
        tags = audio.tags or {}
    return (
        _first(tags, "artist"),
        _first(tags, "album"),
        _first(tags, "title"),
        _first(tags, "albumartist", "album artist"),
        _first_year(tags),
    )


def _from_vorbis_like(audio: object) -> tuple[str, str, str, str, str]:
    return (
        _first(audio, "artist"),
        _first(audio, "album"),
        _first(audio, "title"),
        _first(audio, "albumartist", "album artist"),
        _first_year(audio),
    )


def _from_wave(path: Path) -> tuple[str, str, str, str, str]:
    try:
        audio = WAVE(path)
    except Exception:  # noqa: BLE001
        return "", "", "", "", ""
    if audio.tags is None:
        return "", "", "", "", ""
    # WAVE may carry ID3; use EasyID3-like access when possible
    tags = audio.tags
    artist = _id3_text(tags, "TPE1") or _id3_text(tags, "TPE2")
    album = _id3_text(tags, "TALB")
    title = _id3_text(tags, "TIT2")
    album_artist = _id3_text(tags, "TPE2")
    year = _id3_text(tags, "TDRC") or _id3_text(tags, "TYER")
    return artist, album, title, album_artist, year


def _extract_musicbrainz_ids(path: Path) -> tuple[str, str]:
    """Best-effort MusicBrainz release/artist IDs from tags."""
    try:
        audio = MutagenFile(path, easy=True)
    except Exception:  # noqa: BLE001
        return "", ""
    if audio is None:
        return "", ""
    album_id = _first(
        audio,
        "musicbrainz_albumid",
        "musicbrainz album id",
        "musicbrainz_releaseid",
    )
    artist_id = _first(
        audio,
        "musicbrainz_artistid",
        "musicbrainz artist id",
    )
    return album_id, artist_id


def _tags_from_filename(path: Path) -> LocalAudioTags:
    stem = path.stem
    match = _FILENAME_ARTIST_ALBUM.match(stem)
    if not match:
        # Single token — treat as album title only
        if stem.strip():
            return LocalAudioTags(
                path=path,
                album=stem.strip(),
                source="filename",
            )
        return LocalAudioTags(path=path, source="none")

    return LocalAudioTags(
        path=path,
        artist=match.group("artist").strip(),
        album=match.group("album").strip(),
        source="filename",
    )


def _first(mapping: object, *keys: str) -> str:
    for key in keys:
        try:
            value = mapping[key]  # type: ignore[index]
        except Exception:  # noqa: BLE001
            continue
        if isinstance(value, list | tuple):
            if not value:
                continue
            text = str(value[0]).strip()
        else:
            text = str(value).strip()
        if text:
            return text
    return ""


def _first_year(mapping: object) -> str:
    raw = _first(mapping, "date", "year", "originaldate")
    if not raw:
        return ""
    match = re.search(r"(\d{4})", raw)
    return match.group(1) if match else raw[:4]


def _id3_text(tags: object, frame: str) -> str:
    try:
        values = tags.getall(frame)  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        return ""
    if not values:
        return ""
    text = str(values[0]).strip()
    # mutagen ID3 frames stringify as "TPE1(encoding=<Encoding.UTF8: 3>, text=['x'])"
    if "text=" in text:
        match = re.search(r"text=\['([^']*)'\]", text)
        if match:
            return match.group(1).strip()
    return text
