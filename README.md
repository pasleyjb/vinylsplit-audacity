# VinylSplit for Audacity

**Version 1.1.0** — Stable release

VinylSplit for Audacity helps users digitize vinyl records by generating a complete album layout in Audacity from MusicBrainz metadata, then exporting tagged tracks with artwork.

## Status

Version 1.1.0 streamlines the wizard with waveform lattice editing. Version 1.0.0 was the first stable release: MusicBrainz lookup, region layout generation, layout review, and export with embedded metadata and cover art into album subfolders, plus Linux Snap/Debian/AppImage packages.

## Requirements

- Python 3.14 or later
- A desktop environment with Qt support (Linux, macOS, or Windows)

## Installation

```bash
git clone https://github.com/vinylsplit/vinylsplit-audacity.git
cd vinylsplit-audacity
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Running

```bash
vinylsplit
```

Or:

```bash
python -m vinylsplit
```

## Linux release build

To create portable Linux artifacts (directory bundle, `.tar.gz`, `.AppImage`, `.deb`, and `.snap`):

```bash
pip install -e ".[packaging]"
./packaging/linux/build.sh
```

Outputs land in `dist/`.

```bash
# Debian / Ubuntu
sudo apt install ./dist/vinylsplit_1.1.0-1_amd64.deb

# Snap (classic — required for Audacity mod-script-pipe)
sudo snap install --dangerous --classic ./dist/vinylsplit_1.1.0_amd64.snap
```

See [packaging/linux/README.md](packaging/linux/README.md) for install instructions and
Audacity prerequisites.

## Development

```bash
# Format
black src tests
ruff check --fix src tests

# Test
pytest
```

## Project Structure

```
src/vinylsplit/
├── app.py              # Application entry point
├── core/               # Logging, settings, dependency injection
├── wizard/             # QWizard workflow and pages
├── audacity/           # Audacity integration (planned)
├── musicbrainz/        # MusicBrainz API client (planned)
├── metadata/           # Release and track models (planned)
├── labels/             # Audacity label placement (planned)
├── export/             # Export workflows (planned)
├── ui/                 # Qt Designer .ui files
└── resources/          # Icons, stylesheets, compiled resources
```

## License

MIT — see [LICENSE](LICENSE).