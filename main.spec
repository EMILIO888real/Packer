# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/main/main.py'],
    pathex=['.'], # This allows PyInstaller to see the 'src' directory
    binaries=[],
    datas=[
        ('src/main/assets', 'src/main/assets'), 
        ('src/main/custom_modules', 'src/main/custom_modules'),
        ('src/__init__.py', 'src'),
        ('src/main/__init__.py', 'src/main'),
    ],
    hiddenimports=['src.main.custom_modules', 'src.main.custom_modules.et'],
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Packer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,
)
