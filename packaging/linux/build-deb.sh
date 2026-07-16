#!/usr/bin/env bash
# Build a .deb package from the existing PyInstaller one-directory bundle.
#
# Usage (from repo root, after the bundle exists):
#   ./packaging/linux/build-deb.sh
#
# Or let packaging/linux/build.sh invoke this automatically.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PACKAGING_DIR="${ROOT}/packaging/linux"
DEBIAN_DIR="${PACKAGING_DIR}/debian"
DIST_DIR="${ROOT}/dist"
VENV_PYTHON="${ROOT}/.venv/bin/python"
BUNDLE_NAME="vinylsplit"
PACKAGE_NAME="vinylsplit"
DEBIAN_REVISION="${DEBIAN_REVISION:-1}"

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "Debian packaging is only supported on Linux." >&2
    exit 1
fi

if ! command -v dpkg-deb >/dev/null 2>&1; then
    echo "dpkg-deb is required. Install it with: sudo apt install dpkg" >&2
    exit 1
fi

ARCH="$(uname -m)"
case "${ARCH}" in
    x86_64) DEB_ARCH="amd64" ;;
    aarch64) DEB_ARCH="arm64" ;;
    *)
        echo "Unsupported architecture for .deb: ${ARCH}" >&2
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

DEB_VERSION="${VERSION}-${DEBIAN_REVISION}"
DEB_FILENAME="${PACKAGE_NAME}_${DEB_VERSION}_${DEB_ARCH}.deb"
DEB_PATH="${DIST_DIR}/${DEB_FILENAME}"
STAGING_DIR="${DIST_DIR}/.deb-staging-${PACKAGE_NAME}"
PKG_ROOT="${STAGING_DIR}/${PACKAGE_NAME}"

echo "==> Building Debian package ${DEB_FILENAME}"

rm -rf "${STAGING_DIR}"
mkdir -p \
    "${PKG_ROOT}/DEBIAN" \
    "${PKG_ROOT}/opt/${PACKAGE_NAME}" \
    "${PKG_ROOT}/usr/bin" \
    "${PKG_ROOT}/usr/share/applications" \
    "${PKG_ROOT}/usr/share/icons/hicolor/256x256/apps" \
    "${PKG_ROOT}/usr/share/doc/${PACKAGE_NAME}"

# Application payload under /opt/vinylsplit
cp -a "${BUNDLE_DIR}/." "${PKG_ROOT}/opt/${PACKAGE_NAME}/"
# Drop the portable share tree; desktop integration uses FHS paths below.
rm -rf "${PKG_ROOT}/opt/${PACKAGE_NAME}/share"

# PATH launcher
cat > "${PKG_ROOT}/usr/bin/${PACKAGE_NAME}" <<EOF
#!/bin/sh
exec /opt/${PACKAGE_NAME}/${PACKAGE_NAME} "\$@"
EOF
chmod 755 "${PKG_ROOT}/usr/bin/${PACKAGE_NAME}"
chmod 755 "${PKG_ROOT}/opt/${PACKAGE_NAME}/${PACKAGE_NAME}"

# Desktop entry points at the /usr/bin launcher
install -m 644 "${PACKAGING_DIR}/vinylsplit.desktop" \
    "${PKG_ROOT}/usr/share/applications/vinylsplit.desktop"
sed -i "s|^Exec=.*|Exec=${PACKAGE_NAME}|" \
    "${PKG_ROOT}/usr/share/applications/vinylsplit.desktop"

if [[ -f "${PACKAGING_DIR}/vinylsplit.png" ]]; then
    install -m 644 "${PACKAGING_DIR}/vinylsplit.png" \
        "${PKG_ROOT}/usr/share/icons/hicolor/256x256/apps/vinylsplit.png"
fi

install -m 644 "${DEBIAN_DIR}/copyright" \
    "${PKG_ROOT}/usr/share/doc/${PACKAGE_NAME}/copyright"
install -m 644 "${ROOT}/LICENSE" \
    "${PKG_ROOT}/usr/share/doc/${PACKAGE_NAME}/LICENSE"

# Simple Debian changelog
CHANGELOG_TMP="$(mktemp)"
cat > "${CHANGELOG_TMP}" <<EOF
${PACKAGE_NAME} (${DEB_VERSION}) unstable; urgency=medium

  * Upstream release ${VERSION} packaged for Debian/Ubuntu.

 -- VinylSplit Contributors <noreply@users.noreply.github.com>  $(date -Ru)
EOF
if command -v gzip >/dev/null 2>&1; then
    gzip -9n -c "${CHANGELOG_TMP}" > "${PKG_ROOT}/usr/share/doc/${PACKAGE_NAME}/changelog.Debian.gz"
    chmod 644 "${PKG_ROOT}/usr/share/doc/${PACKAGE_NAME}/changelog.Debian.gz"
else
    install -m 644 "${CHANGELOG_TMP}" \
        "${PKG_ROOT}/usr/share/doc/${PACKAGE_NAME}/changelog.Debian"
fi
rm -f "${CHANGELOG_TMP}"

install -m 755 "${DEBIAN_DIR}/postinst" "${PKG_ROOT}/DEBIAN/postinst"
install -m 755 "${DEBIAN_DIR}/postrm" "${PKG_ROOT}/DEBIAN/postrm"

# Installed size in KiB (exclude DEBIAN control metadata)
INSTALLED_SIZE="$(du -sk --exclude=DEBIAN "${PKG_ROOT}" | cut -f1)"

cat > "${PKG_ROOT}/DEBIAN/control" <<EOF
Package: ${PACKAGE_NAME}
Version: ${DEB_VERSION}
Section: sound
Priority: optional
Architecture: ${DEB_ARCH}
Maintainer: VinylSplit Contributors <noreply@users.noreply.github.com>
Installed-Size: ${INSTALLED_SIZE}
Depends: libc6
Recommends: audacity
Homepage: https://github.com/vinylsplit/vinylsplit-audacity
Description: Vinyl digitization helper for Audacity
 VinylSplit for Audacity helps digitize vinyl records by generating a
 complete album layout in Audacity from MusicBrainz metadata, then
 exporting tagged tracks with embedded artwork.
 .
 This package ships a self-contained application bundle. Audacity is
 recommended and must have mod-script-pipe enabled.
EOF
chmod 644 "${PKG_ROOT}/DEBIAN/control"

# Ensure no stray write bits on control files confuse dpkg
find "${PKG_ROOT}/DEBIAN" -type f -exec chmod u+rw,go+r {} +
chmod 755 "${PKG_ROOT}/DEBIAN/postinst" "${PKG_ROOT}/DEBIAN/postrm"

# Normalize permissions for files copied from the build tree
find "${PKG_ROOT}/opt" -type d -exec chmod 755 {} +
find "${PKG_ROOT}/opt" -type f -exec chmod u+rw,go+r {} +
chmod 755 "${PKG_ROOT}/opt/${PACKAGE_NAME}/${PACKAGE_NAME}"
# Keep bundled shared libraries and native extensions executable where needed
find "${PKG_ROOT}/opt/${PACKAGE_NAME}" \( -name '*.so' -o -name '*.so.*' \) -exec chmod 755 {} + 2>/dev/null || true

rm -f "${DEB_PATH}"
dpkg-deb --root-owner-group --build "${PKG_ROOT}" "${DEB_PATH}"

# Quick structural validation (avoid SIGPIPE from head closing early under pipefail)
dpkg-deb --info "${DEB_PATH}" >/dev/null
dpkg-deb --contents "${DEB_PATH}" >/dev/null

rm -rf "${STAGING_DIR}"

echo "Debian package: ${DEB_PATH}"
echo
echo "Install with:"
echo "  sudo apt install ./${DEB_PATH##${ROOT}/}"
echo "  # or: sudo dpkg -i ${DEB_PATH}"
