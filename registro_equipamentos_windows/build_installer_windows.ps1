# ===============================
# Build Installer (Inno Setup) -> dist_installer
# ===============================
$ErrorActionPreference = "Stop"

Write-Host ">>> Build Installer (Inno Setup) -> dist_installer" -ForegroundColor Cyan

# repo root = pasta acima de registro_equipamentos_windows
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

# caminho do .iss
$IssPath = Join-Path $PSScriptRoot "installer\LeitorCodigos.iss"
if (!(Test-Path $IssPath)) {
  throw ".iss não encontrado em: $IssPath"
}

# build do PyInstaller (NA RAIZ DO REPO)
$PyDist = Join-Path $RepoRoot "dist\LeitorCodigos"
if (!(Test-Path $PyDist)) {
  throw "Pasta do PyInstaller não encontrada: $PyDist. O build do LeitorCodigos não foi gerado."
}

# pasta de saída (na raiz do repo)
$OutDir = Join-Path $RepoRoot "dist_installer"
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

Write-Host "Compilando: $IssPath" -ForegroundColor Yellow
& ISCC.exe $IssPath

Write-Host ">>> OK! Conteúdo de dist_installer:" -ForegroundColor Green
Get-ChildItem $OutDir -Force | Format-Table Name, Length, LastWriteTime
