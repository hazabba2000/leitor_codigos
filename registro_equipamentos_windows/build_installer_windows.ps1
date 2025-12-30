.\build_windows.ps1
& $ISCC ".\installer\installer.iss"

# 1) Build PyInstaller (gera dist\RegistroEquipamentos\...)
.\build_windows.ps1

# 2) Compilar Inno Setup (precisa Inno instalado)
$ISCC = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (!(Test-Path $ISCC)) {
  $ISCC = "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
}

if (!(Test-Path $ISCC)) {
  Write-Host "ERRO: Inno Setup não encontrado. Instale o Inno Setup 6." -ForegroundColor Red
  exit 1
}

& $ISCC ".\installer\installer.iss"
Write-Host "OK -> installer_output\ (Setup.exe gerado)" -ForegroundColor Green
