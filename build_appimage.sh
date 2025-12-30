#!/usr/bin/env bash
set -euo pipefail

# =========================
# CONFIG
# =========================
APP="LeitorCodigos"
SPEC_FILE="${APP}.spec"

# Se seu app usa assets em runtime, deixe 1.
# Se NÃO usa, pode deixar 0 (AppImage fica menor e mais limpo).
INCLUDE_ASSETS="${INCLUDE_ASSETS:-1}"

# Ícone (preferência: 256x256 PNG)
ICON_SRC="${ICON_SRC:-assets/logo_256.png}"  # ajuste se quiser outro
ICON_NAME="leitorcodigos"                    # sem extensão

# Tools (já estão no seu repo)
LINUXDEPLOY="${LINUXDEPLOY:-./tools/linuxdeploy-x86_64.AppImage}"
APPIMAGETOOL="${APPIMAGETOOL:-./tools/appimagetool-x86_64.AppImage}"

# AppDir
APPDIR="${APPDIR:-AppDir}"

# Saída AppImage
OUT_APPIMAGE="${OUT_APPIMAGE:-${APP}-x86_64.AppImage}"

# =========================
# HELPERS
# =========================
die() { echo "❌ $*" >&2; exit 1; }
log() { echo "✅ $*"; }

require_file() {
  [[ -f "$1" ]] || die "Arquivo não encontrado: $1"
}
require_cmd_or_file() {
  [[ -x "$1" ]] || die "Não executável / não encontrado: $1"
}

# =========================
# CHECKS
# =========================
require_file "$SPEC_FILE"
require_cmd_or_file "$LINUXDEPLOY"
require_cmd_or_file "$APPIMAGETOOL"

# =========================
# BUILD (PyInstaller)
# =========================
log "Build com PyInstaller (spec: $SPEC_FILE)"
python -m PyInstaller "$SPEC_FILE"

BIN="dist/${APP}/${APP}"
[[ -f "$BIN" ]] || die "Executável não encontrado em: $BIN"

# =========================
# PREPARE APPDIR
# =========================
log "Preparando AppDir: $APPDIR"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copia executável
log "Copiando binário: $BIN -> $APPDIR/usr/bin/$APP"
install -m 0755 "$BIN" "$APPDIR/usr/bin/$APP"

# Copia _internal (necessário para one-dir do PyInstaller)
# Sem isso, vai dar erro tipo "libpython... cannot open..."
if [[ -d "dist/${APP}/_internal" ]]; then
  log "Copiando pasta _internal"
  cp -a "dist/${APP}/_internal" "$APPDIR/usr/bin/_internal"
else
  # algumas builds ficam como dist/APP/_internal ou dist/APP/APP/_internal
  if [[ -d "dist/${APP}/${APP}/_internal" ]]; then
    log "Copiando pasta _internal (layout alternativo)"
    cp -a "dist/${APP}/${APP}/_internal" "$APPDIR/usr/bin/_internal"
  else
    log "⚠️  _internal não encontrado — se o app falhar no AppImage, isso é o motivo."
  fi
fi

# =========================
# ASSETS (opcional)
# =========================
if [[ "$INCLUDE_ASSETS" == "1" ]]; then
  if [[ -d "assets" ]]; then
    log "Incluindo assets/ no AppImage (runtime)"
    mkdir -p "$APPDIR/usr/share/${APP}/assets"
    cp -a "assets/." "$APPDIR/usr/share/${APP}/assets/"
  else
    log "⚠️  assets/ não existe, pulando."
  fi
else
  log "INCLUDE_ASSETS=0 → não copiando assets/ (build mais portátil e menor)"
fi

# =========================
# ICON
# =========================
if [[ -f "$ICON_SRC" ]]; then
  log "Copiando ícone: $ICON_SRC"
  install -m 0644 "$ICON_SRC" "$APPDIR/usr/share/icons/hicolor/256x256/apps/${ICON_NAME}.png"
else
  log "⚠️  Ícone não encontrado em $ICON_SRC. (linuxdeploy vai reclamar se você passar --icon-file)"
fi

# =========================
# DESKTOP FILE
# =========================
DESKTOP_FILE="$APPDIR/usr/share/applications/${APP}.desktop"
log "Criando .desktop: $DESKTOP_FILE"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=${APP}
Exec=${APP}
Icon=${ICON_NAME}
Categories=Utility;
Terminal=false
EOF

# =========================
# LINUXDEPLOY + APPIMAGETOOL
# =========================
log "Rodando linuxdeploy..."
# só passa --icon-file se existir (evita erro "No such file")
LINUXDEPLOY_ARGS=( --appdir "$APPDIR" --desktop-file "$DESKTOP_FILE" )

if [[ -f "$APPDIR/usr/share/icons/hicolor/256x256/apps/${ICON_NAME}.png" ]]; then
  LINUXDEPLOY_ARGS+=( --icon-file "$APPDIR/usr/share/icons/hicolor/256x256/apps/${ICON_NAME}.png" )
fi

"$LINUXDEPLOY" "${LINUXDEPLOY_ARGS[@]}"

log "Gerando AppImage: $OUT_APPIMAGE"
"$APPIMAGETOOL" "$APPDIR" "$OUT_APPIMAGE"

chmod +x "$OUT_APPIMAGE"
log "AppImage pronto: ./$OUT_APPIMAGE"

# =========================
# SMOKE TEST
# =========================
log "Teste rápido (opcional):"
echo "  ./$OUT_APPIMAGE"
echo "  ou: ./dist/${APP}/${APP}"
