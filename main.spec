# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, copy_metadata

hiddenimports = collect_submodules('packer.custom_modules')

a = Analysis(
    ['src/packer/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[
    ("src/packer/assets", "packer/assets"),
    ] + copy_metadata("twine"),
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='packer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    onefile=True,
    icon='src/packer/assets/images/Packer icon.ico'
)
