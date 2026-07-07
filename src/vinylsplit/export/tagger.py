"""Embed metadata and artwork into exported audio files."""

from __future__ import annotations

import logging
from pathlib import Path

from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, ID3, TALB, TCON, TDRC, TIT2, TPE1, TRCK, Encoding
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
from mutagen.wave import WAVE

from vinylsplit.export.models import TrackExportMetadata
from vinylsplit.metadata.session import AlbumArtwork, ExportFormat

_logger = logging.getLogger(__name__)

_PICTURE_TYPE_COVER_FRONT = 3


def embed_track_metadata(
    path: Path,
    metadata: TrackExportMetadata,
    *,
    export_format: ExportFormat,
    artwork: AlbumArtwork | None = None,
) -> None:
    """Write tags and optional artwork into *path*."""
    if export_format is ExportFormat.FLAC:
        _tag_flac(path, metadata, artwork)
        return
    if export_format is ExportFormat.MP3:
        _tag_mp3(path, metadata, artwork)
        return
    if export_format is ExportFormat.OGG:
        _tag_ogg(path, metadata, artwork)
        return
    if export_format is ExportFormat.WAV:
        _tag_wav(path, metadata, artwork)
        return

    msg = f"Unsupported export format for tagging: {export_format}"
    raise ValueError(msg)


def _tag_flac(
    path: Path,
    metadata: TrackExportMetadata,
    artwork: AlbumArtwork | None,
) -> None:
    audio = FLAC(path)
    _apply_vorbis_tags(audio, metadata)
    if artwork is not None and artwork.is_available:
        picture = Picture()
        picture.type = _PICTURE_TYPE_COVER_FRONT
        picture.mime = artwork.mime_type or "image/jpeg"
        picture.desc = "Cover"
        picture.data = artwork.data or b""
        audio.clear_pictures()
        audio.add_picture(picture)
    audio.save()


def _tag_mp3(
    path: Path,
    metadata: TrackExportMetadata,
    artwork: AlbumArtwork | None,
) -> None:
    audio = MP3(path, ID3=ID3)
    if audio.tags is None:
        audio.add_tags()
    assert audio.tags is not None
    tags = audio.tags
    tags.delall("TIT2")
    tags.delall("TPE1")
    tags.delall("TALB")
    tags.delall("TRCK")
    tags.delall("TCON")
    tags.delall("TDRC")
    tags.add(TIT2(encoding=Encoding.UTF8, text=metadata.title))
    tags.add(TPE1(encoding=Encoding.UTF8, text=metadata.artist))
    tags.add(TALB(encoding=Encoding.UTF8, text=metadata.album))
    tags.add(TRCK(encoding=Encoding.UTF8, text=metadata.track_number))
    if metadata.genre:
        tags.add(TCON(encoding=Encoding.UTF8, text=metadata.genre))
    if metadata.date:
        tags.add(TDRC(encoding=Encoding.UTF8, text=metadata.date))
    _apply_musicbrainz_id3(tags, metadata)
    if artwork is not None and artwork.is_available:
        tags.delall("APIC")
        tags.add(
            APIC(
                encoding=Encoding.UTF8,
                mime=artwork.mime_type or "image/jpeg",
                type=3,
                desc="Cover",
                data=artwork.data or b"",
            )
        )
    audio.save()


def _tag_ogg(
    path: Path,
    metadata: TrackExportMetadata,
    artwork: AlbumArtwork | None,
) -> None:
    audio = OggVorbis(path)
    _apply_vorbis_tags(audio, metadata)
    if artwork is not None and artwork.is_available:
        audio["metadata_block_picture"] = [
            _flac_picture_block(artwork),
        ]
    audio.save()


def _tag_wav(
    path: Path,
    metadata: TrackExportMetadata,
    artwork: AlbumArtwork | None,
) -> None:
    audio = WAVE(path)
    if audio.tags is None:
        audio.add_tags()
    assert audio.tags is not None
    tags = audio.tags
    tags.delall("TIT2")
    tags.delall("TPE1")
    tags.delall("TALB")
    tags.delall("TRCK")
    tags.delall("TCON")
    tags.delall("TDRC")
    tags.add(TIT2(encoding=Encoding.UTF8, text=metadata.title))
    tags.add(TPE1(encoding=Encoding.UTF8, text=metadata.artist))
    tags.add(TALB(encoding=Encoding.UTF8, text=metadata.album))
    tags.add(TRCK(encoding=Encoding.UTF8, text=metadata.track_number))
    if metadata.genre:
        tags.add(TCON(encoding=Encoding.UTF8, text=metadata.genre))
    if metadata.date:
        tags.add(TDRC(encoding=Encoding.UTF8, text=metadata.date))
    _apply_musicbrainz_id3(tags, metadata)
    if artwork is not None and artwork.is_available:
        tags.delall("APIC")
        tags.add(
            APIC(
                encoding=Encoding.UTF8,
                mime=artwork.mime_type or "image/jpeg",
                type=3,
                desc="Cover",
                data=artwork.data or b"",
            )
        )
    audio.save()


def _apply_vorbis_tags(audio, metadata: TrackExportMetadata) -> None:
    audio["artist"] = metadata.artist
    audio["album"] = metadata.album
    audio["title"] = metadata.title
    audio["tracknumber"] = metadata.track_number
    if metadata.genre:
        audio["genre"] = metadata.genre
    if metadata.date:
        audio["date"] = metadata.date
    audio["musicbrainz_albumid"] = metadata.release_id
    if metadata.release_group_id:
        audio["musicbrainz_releasegroupid"] = metadata.release_group_id
    if metadata.artist_id:
        audio["musicbrainz_artistid"] = metadata.artist_id
    if metadata.track_id:
        audio["musicbrainz_trackid"] = metadata.track_id


def _apply_musicbrainz_id3(tags: ID3, metadata: TrackExportMetadata) -> None:
    from mutagen.id3 import TXXX

    tags.delall("TXXX:MusicBrainz Album Id")
    tags.add(
        TXXX(
            encoding=Encoding.UTF8,
            desc="MusicBrainz Album Id",
            text=metadata.release_id,
        )
    )
    if metadata.release_group_id:
        tags.delall("TXXX:MusicBrainz Release Group Id")
        tags.add(
            TXXX(
                encoding=Encoding.UTF8,
                desc="MusicBrainz Release Group Id",
                text=metadata.release_group_id,
            )
        )
    if metadata.artist_id:
        tags.delall("TXXX:MusicBrainz Artist Id")
        tags.add(
            TXXX(
                encoding=Encoding.UTF8,
                desc="MusicBrainz Artist Id",
                text=metadata.artist_id,
            )
        )
    if metadata.track_id:
        tags.delall("TXXX:MusicBrainz Track Id")
        tags.add(
            TXXX(
                encoding=Encoding.UTF8,
                desc="MusicBrainz Track Id",
                text=metadata.track_id,
            )
        )


def _flac_picture_block(artwork: AlbumArtwork) -> str:
    import base64

    picture = Picture()
    picture.type = _PICTURE_TYPE_COVER_FRONT
    picture.mime = artwork.mime_type or "image/jpeg"
    picture.desc = "Cover"
    picture.data = artwork.data or b""
    return base64.b64encode(picture.write()).decode("ascii")