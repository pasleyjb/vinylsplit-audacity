# VinylSplit for Audacity

**Version 0.1** — Foundation release

VinylSplit for Audacity helps users digitize vinyl records by guiding them through splitting tracks inside Audacity using MusicBrainz metadata.

## Status

This is an early foundation release. The wizard UI launches with placeholder pages. MusicBrainz integration, Audacity automation, and export workflows are planned for future versions.

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