# Linux packaging

VinylSplit ships as a self-contained desktop bundle for Linux. It is a companion
app for Audacity and still requires **mod-script-pipe** to be enabled in
Audacity.

## Build

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,packaging]"
chmod +x packaging/linux/build.sh
./packaging/linux/build.sh
```

Artifacts are written to `dist/`:

| Artifact | Description |
|----------|-------------|
| `vinylsplit/` | PyInstaller one-directory bundle |
| `vinylsplit-<version>-linux-<arch>.tar.gz` | Portable archive of the bundle |
| `vinylsplit-<version>-linux-<arch>.AppImage` | Single-file portable app |

Supported architectures: `x86_64`, `aarch64`.

## Install from tarball

```bash
tar -xzf dist/vinylsplit-0.5.2-linux-x86_64.tar.gz -C ~/.local
~/.local/vinylsplit/vinylsplit
```

Optional desktop entry:

```bash
install -Dm644 ~/.local/vinylsplit/share/applications/vinylsplit.desktop \
    ~/.local/share/applications/vinylsplit.desktop
```

Ensure `~/.local/vinylsplit` is on your `PATH`, or edit the desktop file to
use the full executable path.

## Run AppImage

```bash
chmod +x dist/vinylsplit-0.5.2-linux-x86_64.AppImage
./dist/vinylsplit-0.5.2-linux-x86_64.AppImage
```

## End-user prerequisites

1. Install [Audacity](https://www.audacityteam.org/)
2. Enable **mod-script-pipe** in Edit → Preferences → Modules
3. Restart Audacity
4. Launch Audacity before starting VinylSplit