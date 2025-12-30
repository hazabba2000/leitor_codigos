# ===============================
# Build Installer (Inno Setup) -> dist_installer
# ===============================
$ErrorActionPreference = "Stop"

Write-Host ">>> Build Installer (Inno Setup) -> dist_installer" -ForegroundColor Cyan

$IssPath = Join-Path $PSScriptRoot "installer\RegistroEquipamentos.iss"

# Confere se o build do PyInstaller existe
$PyDist = Join-Path $PSScriptRoot "dist\RegistroEquipamentos"
if (!(Test-Path $PyDist)) {
  throw "Pasta do PyInstaller não encontrada: $PyDist. Rode o build_windows.ps1 antes."
}

# Garante pasta de saída (não atrapalha o Inno)
$OutDir = Join-Path $PSScriptRoot "dist_installer"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

# Instala Inno Setup (ISCC) via Chocolatey se não existir
if (-not (Get-Command "ISCC.exe" -ErrorAction SilentlyContinue)) {
  Write-Host "ISCC.exe não encontrado. Instalando Inno Setup via Chocolatey..." -ForegroundColor Yellow

  if (-not (Get-Command "choco.exe" -ErrorAction SilentlyContinue)) {
    Write-Host "Chocolatey não encontrado. Instalando Chocolatey..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
  }

  choco install innosetup -y --no-progress
}

if (!(Test-Path $IssPath)) {
  throw ".iss não encontrado em: $IssPath"
}

Write-Host "Compilando: $IssPath" -ForegroundColor Yellow
& ISCC.exe $IssPath

Write-Host ">>> OK! Conteúdo de dist_installer:" -ForegroundColor Green
Get-ChildItem $OutDir -Force | Format-Table Name, Length, LastWriteTime


