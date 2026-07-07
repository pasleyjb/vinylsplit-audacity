# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for VinylSplit on Linux."""

from __future__ import annotations

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

project_root = Path(SPECPATH).resolve().parents[1]
src_root = project_root / "src"
launcher = Path(SPECPATH) / "launcher.py"

block_cipher = None

hiddenimports = [
    *collect_submodules("mutagen"),
    "requests",
    "certifi",
    "charset_normalizer",
    "idna",
    "urllib3",
]

a = Analysis(
    [str(launcher)],
    pathex=[str(src_root)],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="vinylsplit",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="vinylsplit",
)

if sys.platform != "linux":
    raise SystemExit("packaging/linux/vinylsplit.spec is intended for Linux builds only.")