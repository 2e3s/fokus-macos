# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files


project_root = Path.cwd()
bundle_icon = os.environ.get("FOKUS_BUNDLE_ICON")

a = Analysis(
    ["src/fokus_macos/__main__.py"],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=collect_data_files("fokus_macos"),
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Fokus",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
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
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Fokus",
)
app = BUNDLE(
    coll,
    name="Fokus.app",
    icon=bundle_icon,
    bundle_identifier="com.dv.fokus.macos",
)
