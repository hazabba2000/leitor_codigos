#!/usr/bin/env bash
set -euo pipefail

APP="LeitorCodigos"
DIST_DIR="dist/${APP}"
APPDIR="AppDir"

# 0) sanity
test -f "${DIST_DIR}/${APP}" || { echo "ERRO: não achei ${DIST_DIR}/${APP}. Rode o PyInstaller antes."; exit 1; }
test -d "${DIST_DIR}/_internal" || { echo "ERRO: não achei ${DIST_DIR}/_internal. Build do PyInstaller está incompleto."; exit 1; }

# 1) limpa AppDir
rm -rf "${APPDIR}"
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/applications"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

# 2) copia BIN + _internal (essencial!)
cp -a "${DIST_DIR}/${APP}" "${APPDIR}/usr/bin/${APP}"
cp -a "${DIST_DIR}/_internal" "${APPDIR}/usr/bin/_internal"

# 3) ícone (ajuste se quiser outro)
ICON_SRC="assets/logo_256.png"
test -f "${ICON_SRC}" || ICON_SRC="$(ls -1 assets/*.png | head -n 1)"
cp -a "${ICON_SRC}" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/leitorcodigos.png"

# 4) desktop file (sem sudo, sempre dentro do AppDir)
cat > "${APPDIR}/usr/share/applications/LeitorCodigos.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=LeitorCodigos
Exec=LeitorCodigos
Icon=leitorcodigos
Categories=Utility;
Terminal=false
EOF

# 5) ferramentas (ou usa as do repo; se não existir, baixa)
mkdir -p tools

if [[ ! -f tools/linuxdeploy-x86_64.AppImage ]]; then
  curl -L -o tools/linuxdeploy-x86_64.AppImage \
    https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
fi

if [[ ! -f tools/appimagetool-x86_64.AppImage ]]; then
  curl -L -o tools/appimagetool-x86_64.AppImage \
    https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
fi

chmod +x tools/linuxdeploy-x86_64.AppImage tools/appimagetool-x86_64.AppImage

# 6) gera AppImage
./tools/linuxdeploy-x86_64.AppImage \
  --appdir "${APPDIR}" \
  --desktop-file "${APPDIR}/usr/share/applications/LeitorCodigos.desktop" \
  --icon-file "${APPDIR}/usr/share/icons/hicolor/256x256/apps/leitorcodigos.png"

./tools/appimagetool-x86_64.AppImage "${APPDIR}" "${APP}-x86_64.AppImage"

echo "OK: gerado ${APP}-x86_64.AppImage"
