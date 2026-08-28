# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files


datas = collect_data_files("customtkinter")
datas += collect_data_files("uiautomation")
datas += collect_data_files("faster_whisper")
datas += [
    ("moneypenny.ico", "."),
    ("moneypenny icon.png", "."),
]

a = Analysis(
    ["voice_to_text.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=["gui", "uiautomation"],
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
    name="MoneyPenny",
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
    icon=["moneypenny.ico"],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MoneyPenny",
)
