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
| `vinylsplit_<version>-1_<debarch>.deb` | Debian/Ubuntu package (`amd64` / `arm64`) |

Supported architectures: `x86_64` (`amd64`), `aarch64` (`arm64`).

### Debian package only

If the PyInstaller bundle already exists under `dist/vinylsplit/`:

```bash
./packaging/linux/build-deb.sh
```

Requires `dpkg-deb` (from the `dpkg` package).

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

## Install from .deb

```bash
sudo apt install ./dist/vinylsplit_0.5.2-1_amd64.deb
# or:
sudo dpkg -i dist/vinylsplit_0.5.2-1_amd64.deb
```

This installs:

| Path | Purpose |
|------|---------|
| `/opt/vinylsplit/` | Self-contained application bundle |
| `/usr/bin/vinylsplit` | Launcher on `PATH` |
| `/usr/share/applications/vinylsplit.desktop` | Desktop menu entry |
| `/usr/share/icons/hicolor/256x256/apps/vinylsplit.png` | Application icon |

Remove with:

```bash
sudo apt remove vinylsplit
```

## End-user prerequisites

1. Install [Audacity](https://www.audacityteam.org/)
2. Enable **mod-script-pipe** in Edit → Preferences → Modules
3. Restart Audacity
4. Launch Audacity before starting VinylSplit