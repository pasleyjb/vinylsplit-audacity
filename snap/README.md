# Snap packaging

VinylSplit is packaged as a **classic** snap so it can talk to a host
Audacity instance via mod-script-pipe FIFOs under `/tmp`.

## Build

From the repository root, after the PyInstaller bundle exists:

```bash
./packaging/linux/build.sh          # full Linux release (includes snap)
# or
./packaging/linux/build-snap.sh     # snap only (needs dist/vinylsplit/)
```

Output: `dist/vinylsplit_<version>_amd64.snap`

## Local install

```bash
sudo snap install --dangerous --classic dist/vinylsplit_1.0.0_amd64.snap
vinylsplit
```

## Snap Store

1. `sudo snap install snapcraft --classic`
2. `snapcraft login`
3. `snapcraft register vinylsplit`
4. Open a **classic confinement** request on the
   [Snapcraft forum](https://forum.snapcraft.io/c/store-requests/) explaining
   the Audacity `/tmp` pipe requirement.
5. After approval:

```bash
snapcraft upload --release=edge dist/vinylsplit_1.0.0_amd64.snap
# later:
snapcraft release vinylsplit <revision> stable
```

Users then install with:

```bash
sudo snap install vinylsplit --classic
```

## Layout

| Path | Purpose |
|------|---------|
| `snap/snapcraft.yaml` | Snapcraft recipe (when `snapcraft` is installed) |
| `snap/gui/` | Desktop entry, icon, AppStream metainfo |
| `packaging/linux/build-snap.sh` | Builds `.snap` from the PyInstaller bundle |
