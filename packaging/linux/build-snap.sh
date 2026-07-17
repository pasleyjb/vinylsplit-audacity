#!/usr/bin/env bash
# Build a classic Snap package from the PyInstaller one-directory bundle.
#
# Usage (from repo root, after dist/vinylsplit exists):
#   ./packaging/linux/build-snap.sh
#
# Assembles a valid .snap with mksquashfs from the PyInstaller bundle
# (no LXD/Multipass required). Set USE_SNAPCRAFT=1 to try snapcraft first.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PACKAGING_DIR="${ROOT}/packaging/linux"
SNAP_DIR="${ROOT}/snap"
DIST_DIR="${ROOT}/dist"
VENV_PYTHON="${ROOT}/.venv/bin/python"
BUNDLE_NAME="vinylsplit"
SNAP_NAME="vinylsplit"

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "Snap packaging is only supported on Linux." >&2
    exit 1
fi

ARCH="$(uname -m)"
case "${ARCH}" in
    x86_64) SNAP_ARCH="amd64" ;;
    aarch64) SNAP_ARCH="arm64" ;;
    *)
        echo "Unsupported architecture for snap: ${ARCH}" >&2
        exit 1
        ;;
esac

if [[ -x "${VENV_PYTHON}" ]]; then
    VERSION="$("${VENV_PYTHON}" -c "from vinylsplit import __version__; print(__version__)")"
elif [[ -f "${ROOT}/src/vinylsplit/__init__.py" ]]; then
    VERSION="$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "${ROOT}/src/vinylsplit/__init__.py" | head -1)"
else
    echo "Unable to determine package version." >&2
    exit 1
fi

if [[ -z "${VERSION}" ]]; then
    echo "Unable to determine package version." >&2
    exit 1
fi

BUNDLE_DIR="${DIST_DIR}/${BUNDLE_NAME}"
if [[ ! -x "${BUNDLE_DIR}/${BUNDLE_NAME}" ]]; then
    echo "PyInstaller bundle not found at ${BUNDLE_DIR}/${BUNDLE_NAME}" >&2
    echo "Build it first with: ./packaging/linux/build.sh" >&2
    exit 1
fi

if [[ ! -f "${SNAP_DIR}/gui/vinylsplit.png" ]]; then
    if [[ -f "${PACKAGING_DIR}/vinylsplit.png" ]]; then
        mkdir -p "${SNAP_DIR}/gui"
        cp -f "${PACKAGING_DIR}/vinylsplit.png" "${SNAP_DIR}/gui/vinylsplit.png"
    else
        echo "Missing snap icon at ${SNAP_DIR}/gui/vinylsplit.png" >&2
        exit 1
    fi
fi

SNAP_FILENAME="${SNAP_NAME}_${VERSION}_${SNAP_ARCH}.snap"
SNAP_PATH="${DIST_DIR}/${SNAP_FILENAME}"
PRIME_DIR="${DIST_DIR}/.snap-prime"

echo "==> Building Snap package ${SNAP_FILENAME}"

# Keep snapcraft.yaml version in sync when present
if [[ -f "${SNAP_DIR}/snapcraft.yaml" ]]; then
    if grep -qE "^version:" "${SNAP_DIR}/snapcraft.yaml"; then
        sed -i "s/^version:.*/version: '${VERSION}'/" "${SNAP_DIR}/snapcraft.yaml"
    fi
fi

build_with_mksquashfs() {
    if ! command -v mksquashfs >/dev/null 2>&1; then
        echo "mksquashfs is required (package: squashfs-tools)." >&2
        exit 1
    fi

    echo "==> Assembling snap with mksquashfs"
    rm -rf "${PRIME_DIR}"
    mkdir -p \
        "${PRIME_DIR}/meta/gui" \
        "${PRIME_DIR}/opt/${SNAP_NAME}" \
        "${PRIME_DIR}/usr/share/metainfo"

    # Application payload (must keep vinylsplit next to _internal)
    cp -a "${BUNDLE_DIR}/." "${PRIME_DIR}/opt/${SNAP_NAME}/"
    rm -rf "${PRIME_DIR}/opt/${SNAP_NAME}/share"
    chmod 755 "${PRIME_DIR}/opt/${SNAP_NAME}/${SNAP_NAME}"

    # Desktop + icon for snapd / App Center
    install -m 644 "${SNAP_DIR}/gui/vinylsplit.desktop" \
        "${PRIME_DIR}/meta/gui/vinylsplit.desktop"
    install -m 644 "${SNAP_DIR}/gui/vinylsplit.png" \
        "${PRIME_DIR}/meta/gui/vinylsplit.png"

    if [[ -f "${SNAP_DIR}/gui/vinylsplit.metainfo.xml" ]]; then
        install -m 644 "${SNAP_DIR}/gui/vinylsplit.metainfo.xml" \
            "${PRIME_DIR}/usr/share/metainfo/io.github.pasleyjb.vinylsplit.metainfo.xml"
        # Keep AppStream release version aligned (first release version= only)
        sed -i "0,/version=\"[0-9.]*\"/s//version=\"${VERSION}\"/" \
            "${PRIME_DIR}/usr/share/metainfo/io.github.pasleyjb.vinylsplit.metainfo.xml" || true
    fi

    cat > "${PRIME_DIR}/meta/snap.yaml" <<EOF
name: ${SNAP_NAME}
version: '${VERSION}'
summary: Vinyl digitization helper for Audacity
description: |
  VinylSplit for Audacity helps digitize vinyl records by generating a
  complete album layout in Audacity from MusicBrainz metadata, then
  exporting tagged tracks with embedded artwork.

  Prerequisites:
    1. Install Audacity
    2. Enable mod-script-pipe in Edit → Preferences → Modules
    3. Restart Audacity, then launch VinylSplit

  Classic confinement is required so VinylSplit can reach Audacity's
  mod-script-pipe FIFOs under the host /tmp directory.
architectures:
- ${SNAP_ARCH}
base: core24
apps:
  ${SNAP_NAME}:
    command: opt/${SNAP_NAME}/${SNAP_NAME}
    common-id: io.github.pasleyjb.vinylsplit
confinement: classic
grade: stable
license: MIT
links:
  contact:
  - https://github.com/pasleyjb/vinylsplit-audacity/issues
  issues:
  - https://github.com/pasleyjb/vinylsplit-audacity/issues
  source-code:
  - https://github.com/pasleyjb/vinylsplit-audacity
  website:
  - https://github.com/pasleyjb/vinylsplit-audacity
EOF

    rm -f "${SNAP_PATH}"
    mksquashfs "${PRIME_DIR}" "${SNAP_PATH}" \
        -noappend \
        -comp lzo \
        -all-root \
        -no-xattrs \
        -no-fragments

    rm -rf "${PRIME_DIR}"
}

if [[ "${USE_SNAPCRAFT:-0}" == "1" ]] && command -v snapcraft >/dev/null 2>&1; then
    echo "==> Using snapcraft (USE_SNAPCRAFT=1)"
    if (
        cd "${ROOT}"
        snapcraft clean --destructive-mode 2>/dev/null || true
        snapcraft pack --destructive-mode --output "${SNAP_PATH}"
    ); then
        if [[ ! -f "${SNAP_PATH}" ]]; then
            found="$(find "${ROOT}" -maxdepth 2 -name "${SNAP_FILENAME}" -type f | head -1 || true)"
            if [[ -n "${found}" ]]; then
                mv -f "${found}" "${SNAP_PATH}"
            fi
        fi
    else
        echo "==> snapcraft failed; falling back to mksquashfs"
        build_with_mksquashfs
    fi
else
    build_with_mksquashfs
fi

if [[ ! -f "${SNAP_PATH}" ]]; then
    echo "Failed to produce ${SNAP_PATH}" >&2
    exit 1
fi

echo "Snap package: ${SNAP_PATH}"
echo
echo "Install locally (classic confinement):"
echo "  sudo snap install --dangerous --classic ${SNAP_PATH}"
echo
echo "Publish to the Snap Store (after name registration + classic approval):"
echo "  snapcraft login"
echo "  snapcraft register ${SNAP_NAME}"
echo "  snapcraft upload --release=edge ${SNAP_PATH}"
echo
echo "Note: classic confinement requires a store-requests review before stable."
