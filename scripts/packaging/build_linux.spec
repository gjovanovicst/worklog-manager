# -*- mode: python ; coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path


def _resolve_spec_dir() -> Path:
    spec_file = globals().get("__file__")
    if spec_file:
        return Path(spec_file).resolve().parent
    for arg in sys.argv:
        if arg.lower().endswith(".spec"):
            return Path(arg).resolve().parent
    return Path.cwd()


SPEC_DIR = _resolve_spec_dir()
if str(SPEC_DIR) not in sys.path:
    sys.path.insert(0, str(SPEC_DIR))

from PyInstaller.utils.hooks import collect_submodules, copy_metadata

from pyinstaller_settings import (
    APP_NAME,
    ENTRY_POINT,
    PROJECT_ROOT,
    base_datas,
    build_path,
    dist_path,
    get_icon,
)

block_cipher = None

distpath = str(dist_path())
workpath = str(build_path())


def _safe_collect(package: str):
    try:
        return collect_submodules(package)
    except Exception:
        return []


def _safe_metadata(package: str):
    try:
        return copy_metadata(package)
    except Exception:
        return []


datas = base_datas()
datas += _safe_metadata("plyer")
datas += _safe_metadata("reportlab")

hiddenimports = []
hiddenimports += _safe_collect("plyer.platforms.linux")
hiddenimports += _safe_collect("plyer.platforms.linux.libs")
hiddenimports += _safe_collect("reportlab.lib")

seen = set()
hiddenimports = [module for module in hiddenimports if not (module in seen or seen.add(module))]

analysis = Analysis(
    [str(ENTRY_POINT)],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
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

pyz = PYZ(analysis.pure, analysis.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    [],
    name=f"{APP_NAME}.bin",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=get_icon("linux"),
)

coll = COLLECT(
    exe,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)
