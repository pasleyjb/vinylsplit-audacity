#!/usr/bin/env bash
# Build VinylSplit Linux release artifacts (directory bundle, tarball, AppImage).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PACKAGING_DIR="${ROOT}/packaging/linux"
DIST_DIR="${ROOT}/dist"
BUILD_DIR="${ROOT}/build"
PYTHON="${ROOT}/.venv/bin/python"
APPIMAGE_TOOL_TAG="continuous"

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "This build script only supports Linux." >&2
    exit 1
fi

ARCH="$(uname -m)"
case "${ARCH}" in
    x86_64) ARCH_LABEL="x86_64" ;;
    aarch64) ARCH_LABEL="aarch64" ;;
    *)
        echo "Unsupported architecture: ${ARCH}" >&2
        exit 1
        ;;
esac

if [[ ! -x "${PYTHON}" ]]; then
    if command -v python >/dev/null 2>&1; then
        PYTHON="$(command -v python)"
    elif command -v python3 >/dev/null 2>&1; then
        PYTHON="$(command -v python3)"
    else
        echo "Python is required. Create a venv or install Python 3.14+." >&2
        exit 1
    fi
fi

echo "==> Installing packaging dependencies"
"${PYTHON}" -m pip install -q -e "${ROOT}[packaging]"

if [[ ! -f "${PACKAGING_DIR}/vinylsplit.png" ]]; then
    echo "==> Generating application icon"
    QT_QPA_PLATFORM=offscreen "${PYTHON}" "${PACKAGING_DIR}/generate_icon.py"
fi

VERSION="$("${PYTHON}" -c "from vinylsplit import __version__; print(__version__)")"
BUNDLE_NAME="vinylsplit"
RELEASE_BASE="${BUNDLE_NAME}-${VERSION}-linux-${ARCH_LABEL}"
TARBALL_PATH="${DIST_DIR}/${RELEASE_BASE}.tar.gz"
APPDIR_PATH="${DIST_DIR}/${RELEASE_BASE}.AppDir"
APPIMAGE_PATH="${DIST_DIR}/${RELEASE_BASE}.AppImage"

echo "==> Building ${VERSION} for linux-${ARCH_LABEL}"
rm -rf "${DIST_DIR}/${BUNDLE_NAME}" "${APPDIR_PATH}" "${APPIMAGE_PATH}"
mkdir -p "${DIST_DIR}" "${BUILD_DIR}"

"${PYTHON}" -m PyInstaller \
    "${PACKAGING_DIR}/vinylsplit.spec" \
    --distpath "${DIST_DIR}" \
    --workpath "${BUILD_DIR}/pyinstaller" \
    --noconfirm

BUNDLE_DIR="${DIST_DIR}/${BUNDLE_NAME}"
if [[ ! -x "${BUNDLE_DIR}/${BUNDLE_NAME}" ]]; then
    echo "Expected bundle executable at ${BUNDLE_DIR}/${BUNDLE_NAME}" >&2
    exit 1
fi

install -Dm644 "${PACKAGING_DIR}/vinylsplit.desktop" \
    "${BUNDLE_DIR}/share/applications/vinylsplit.desktop"
sed -i "s|^Exec=.*|Exec=${BUNDLE_NAME}|" "${BUNDLE_DIR}/share/applications/vinylsplit.desktop"

if [[ -f "${PACKAGING_DIR}/vinylsplit.png" ]]; then
    install -Dm644 "${PACKAGING_DIR}/vinylsplit.png" \
        "${BUNDLE_DIR}/share/icons/hicolor/256x256/apps/vinylsplit.png"
fi

echo "==> Creating tarball ${TARBALL_PATH}"
tar -C "${DIST_DIR}" -czf "${TARBALL_PATH}" "${BUNDLE_NAME}"

echo "==> Preparing AppDir ${APPDIR_PATH}"
rm -rf "${APPDIR_PATH}"
mkdir -p "${APPDIR_PATH}/usr/bin" "${APPDIR_PATH}/usr/share/applications"

cp -a "${BUNDLE_DIR}" "${APPDIR_PATH}/usr/bin/${BUNDLE_NAME}"
install -Dm644 "${PACKAGING_DIR}/vinylsplit.desktop" \
    "${APPDIR_PATH}/vinylsplit.desktop"
install -Dm644 "${PACKAGING_DIR}/vinylsplit.desktop" \
    "${APPDIR_PATH}/usr/share/applications/vinylsplit.desktop"
sed -i "s|^Exec=.*|Exec=${BUNDLE_NAME}|" "${APPDIR_PATH}/vinylsplit.desktop"
sed -i "s|^Exec=.*|Exec=${BUNDLE_NAME}|" "${APPDIR_PATH}/usr/share/applications/vinylsplit.desktop"

if [[ -f "${PACKAGING_DIR}/vinylsplit.png" ]]; then
    install -Dm644 "${PACKAGING_DIR}/vinylsplit.png" "${APPDIR_PATH}/vinylsplit.png"
    install -Dm644 "${PACKAGING_DIR}/vinylsplit.png" \
        "${APPDIR_PATH}/usr/share/icons/hicolor/256x256/apps/vinylsplit.png"
fi

cat > "${APPDIR_PATH}/AppRun" <<'EOF'
#!/bin/sh
set -eu
APPDIR="$(dirname "$(readlink -f "$0")")"
exec "${APPDIR}/usr/bin/vinylsplit/vinylsplit" "$@"
EOF
chmod +x "${APPDIR_PATH}/AppRun"

APPIMAGE_TOOL="${BUILD_DIR}/appimagetool-${ARCH_LABEL}.AppImage"
if [[ ! -x "${APPIMAGE_TOOL}" ]]; then
    echo "==> Downloading appimagetool"
    mkdir -p "${BUILD_DIR}"
    curl -fsSL \
        -o "${APPIMAGE_TOOL}" \
        "https://github.com/AppImage/appimagetool/releases/download/${APPIMAGE_TOOL_TAG}/appimagetool-${ARCH_LABEL}.AppImage"
    chmod +x "${APPIMAGE_TOOL}"
fi

echo "==> Creating AppImage ${APPIMAGE_PATH}"
ARCH="${ARCH}" "${APPIMAGE_TOOL}" "${APPDIR_PATH}" "${APPIMAGE_PATH}"

DEB_PATH=""
if command -v dpkg-deb >/dev/null 2>&1; then
    echo "==> Creating Debian package"
    "${PACKAGING_DIR}/build-deb.sh"
    case "${ARCH_LABEL}" in
        x86_64) _deb_arch="amd64" ;;
        aarch64) _deb_arch="arm64" ;;
        *) _deb_arch="${ARCH_LABEL}" ;;
    esac
    DEB_PATH="${DIST_DIR}/vinylsplit_${VERSION}-1_${_deb_arch}.deb"
else
    echo "==> Skipping .deb (dpkg-deb not found)"
fi

SNAP_PATH=""
if command -v mksquashfs >/dev/null 2>&1 || command -v snapcraft >/dev/null 2>&1; then
    echo "==> Creating Snap package"
    "${PACKAGING_DIR}/build-snap.sh"
    case "${ARCH_LABEL}" in
        x86_64) _snap_arch="amd64" ;;
        aarch64) _snap_arch="arm64" ;;
        *) _snap_arch="${ARCH_LABEL}" ;;
    esac
    SNAP_PATH="${DIST_DIR}/vinylsplit_${VERSION}_${_snap_arch}.snap"
else
    echo "==> Skipping .snap (mksquashfs/snapcraft not found)"
fi

echo
echo "Build complete:"
echo "  Bundle:    ${BUNDLE_DIR}"
echo "  Tarball:   ${TARBALL_PATH}"
echo "  AppImage:  ${APPIMAGE_PATH}"
if [[ -n "${DEB_PATH}" && -f "${DEB_PATH}" ]]; then
    echo "  Deb:       ${DEB_PATH}"
fi
if [[ -n "${SNAP_PATH}" && -f "${SNAP_PATH}" ]]; then
    echo "  Snap:      ${SNAP_PATH}"
fi
echo
echo "Prerequisites for end users:"
echo "  1. Install Audacity"
echo "  2. Enable mod-script-pipe in Edit -> Preferences -> Modules"
echo "  3. Start Audacity, then launch VinylSplit"