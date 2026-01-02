#!/usr/bin/env bash
set -euo pipefail

APP="LeitorCodigos"
APPDIR="AppDir"

# 1) Build (garante que exista dist/LeitorCodigos)
python -m PyInstaller --noconfirm "${APP}.spec"

# 2) Confere saída real
if [ ! -f "dist/${APP}/${APP}" ]; then
  echo "ERRO: não achei dist/${APP}/${APP}. Verifique o PyInstaller."
  ls -lah "dist/${APP}" || true
  exit 1
fi

# 2.1) Garantia extra: libpython dentro do _internal (a prova de outra máquina)
if [ -d "dist/${APP}/_internal" ]; then
  if ! ls "dist/${APP}/_internal"/libpython*.so* >/dev/null 2>&1; then
    echo "AVISO: libpython não encontrada em dist/${APP}/_internal. Tentando copiar do Python do ambiente..."
    LIBPY="$(python - <<'PY'
import sysconfig, os, glob
libdir = sysconfig.get_config_var("LIBDIR") or ""
ldlib  = sysconfig.get_config_var("LDLIBRARY") or ""
cands = []
if libdir and ldlib:
    cands.append(os.path.join(libdir, ldlib))
# tenta variações comuns
cands += glob.glob(os.path.join(libdir, "libpython*.so*"))
# filtra existentes e imprime o primeiro
for p in cands:
    if p and os.path.exists(p):
        print(p)
        break
PY
)"
    if [ -n "${LIBPY:-}" ] && [ -f "${LIBPY}" ]; then
      cp -av "${LIBPY}" "dist/${APP}/_internal/"
      echo "OK: copiei ${LIBPY} para dist/${APP}/_internal/"
    else
      echo "AVISO: não consegui localizar libpython automaticamente. (Pode não ser necessário no seu caso.)"
    fi
  fi
fi

# 3) Monta AppDir
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"

# Copia o executável E o _internal (sem isso quebra PIL/libpython etc.)
cp -a "dist/${APP}/${APP}" "$APPDIR/usr/bin/${APP}"
if [ -d "dist/${APP}/_internal" ]; then
  cp -a "dist/${APP}/_internal" "$APPDIR/usr/bin/_internal"
fi

# 4) Desktop file
mkdir -p "$APPDIR/usr/share/applications"
cat > "$APPDIR/usr/share/applications/${APP}.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=${APP}
Exec=${APP}
Icon=leitorcodigos
Categories=Utility;
Terminal=false
EOF

# 5) Ícone
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
cp -f "assets/logo_256.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/leitorcodigos.png"

# 6) AppImage
chmod +x tools/*.AppImage || true

./tools/linuxdeploy-x86_64.AppImage \
  --appdir "$APPDIR" \
  --desktop-file "$APPDIR/usr/share/applications/${APP}.desktop" \
  --icon-file "$APPDIR/usr/share/icons/hicolor/256x256/apps/leitorcodigos.png"

./tools/appimagetool-x86_64.AppImage "$APPDIR" "${APP}-x86_64.AppImage"
echo "OK: gerado ${APP}-x86_64.AppImage"
