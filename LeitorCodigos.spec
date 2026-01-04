# LeitorCodigos.spec
# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

# roda a partir da raiz do repo (cwd no CI)
datas = [
    ("assets", "assets"),
    ("data/equipamentos_template.db", "."),  # <- 1) pega do /data e coloca no ROOT do bundle
]

binaries = []
hiddenimports = ['passlib', 'passlib.handlers.pbkdf2', "PIL._tkinter_finder", "PIL.ImageTk"]

tmp_ret = collect_all("PIL")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

a = Analysis(
    ["main.py"],
    pathex=[],
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
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="LeitorCodigos",
)
