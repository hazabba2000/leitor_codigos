# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
from pathlib import Path

project_dir = Path(__file__).resolve().parent

# Inclui tudo que está em assets/ (imagens, temas, etc.)
datas = [
    ('assets', 'assets'),
    ('equipamentos_template.db', '.'),
]

binaries = []
hiddenimports = ["PIL._tkinter_finder", "PIL.ImageTk"]

# Bundle completo do Pillow (PIL) para evitar erro no runtime
tmp_datas, tmp_bins, tmp_hidden = collect_all("PIL")
datas += tmp_datas
binaries += tmp_bins
hiddenimports += tmp_hidden

a = Analysis(
    ["main.py"],
    pathex=[str(project_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name="LeitorCodigos",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,          # no Linux, o PyInstaller pode desabilitar UPX automaticamente no CI (ok)
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
    upx=False,
    upx_exclude=[],
    name="LeitorCodigos",
)
