#!/usr/bin/env bash
# Publish the local VinylSplit .snap to the Snap Store.
#
# Prerequisites (run once):
#   sudo snap install snapcraft --classic
#   snapcraft login
#   snapcraft register vinylsplit
#   # File a classic confinement request:
#   # https://forum.snapcraft.io/c/store-requests/15
#
# Usage:
#   ./scripts/publish-snap-store.sh              # upload edge
#   ./scripts/publish-snap-store.sh stable       # release channel
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHANNEL="${1:-edge}"
VERSION="$("${ROOT}/.venv/bin/python" -c "from vinylsplit import __version__; print(__version__)" 2>/dev/null \
  || sed -n 's/^__version__ = "\(.*\)"/\1/p' "${ROOT}/src/vinylsplit/__init__.py" | head -1)"
SNAP_PATH="${ROOT}/dist/vinylsplit_${VERSION}_amd64.snap"

if ! command -v snapcraft >/dev/null 2>&1; then
    echo "snapcraft is not installed. Run:" >&2
    echo "  sudo snap install snapcraft --classic" >&2
    exit 1
fi

if [[ ! -f "${SNAP_PATH}" ]]; then
    echo "Missing ${SNAP_PATH}" >&2
    echo "Build first: ./packaging/linux/build-snap.sh" >&2
    exit 1
fi

echo "==> Uploading ${SNAP_PATH} to channel: ${CHANNEL}"
snapcraft upload --release="${CHANNEL}" "${SNAP_PATH}"

echo
echo "Done. Install with:"
echo "  sudo snap install vinylsplit --classic --channel=${CHANNEL}"
echo
echo "If classic confinement is not yet approved, the store will reject"
echo "stable/candidate releases until the store-requests thread is accepted."
