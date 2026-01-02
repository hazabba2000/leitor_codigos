# registro_equipamentos_windows/build_windows.ps1
Write-Host ">>> Build Windows - LeitorCodigos" -ForegroundColor Cyan
$ErrorActionPreference = "Stop"

# ir para a raiz do repo (funciona no GitHub Actions e local)
Set-Location (Resolve-Path (Join-Path $PSScriptRoot ".."))

# pip
python -m pip install --upgrade pip

# deps (se existir requirements.txt)
if (Test-Path ".\requirements.txt") {
  pip install -r .\requirements.txt
} else {
  Write-Host "requirements.txt não existe, pulando..." -ForegroundColor Yellow
}

pip install pyinstaller

# valida template db no /data
if (-not (Test-Path ".\data\equipamentos_template.db")) {
  throw "data\equipamentos_template.db não encontrado. Commitou o template?"
}

# limpa
if (Test-Path ".\build") { Remove-Item -Recurse -Force .\build }
if (Test-Path ".\dist")  { Remove-Item -Recurse -Force .\dist }

# build com spec (mais consistente)
if (-not (Test-Path ".\LeitorCodigos.spec")) {
  throw "LeitorCodigos.spec não encontrado na raiz do repo."
}

Write-Host "Rodando PyInstaller via .spec..." -ForegroundColor Yellow
python -m PyInstaller --noconfirm .\LeitorCodigos.spec

Write-Host ">>> BUILD CONCLUÍDO!" -ForegroundColor Green
Write-Host "Pasta final: dist\LeitorCodigos" -ForegroundColor Green


