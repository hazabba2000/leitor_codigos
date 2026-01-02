# ===============================
# Build Windows - LeitorCodigos
# ===============================

Write-Host ">>> Build Windows - LeitorCodigos" -ForegroundColor Cyan

# Usar o Python do runner (actions/setup-python) e NÃO criar venv aqui.
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Limpar builds antigos
if (Test-Path "build") { Remove-Item -Recurse -Force build }
if (Test-Path "dist")  { Remove-Item -Recurse -Force dist }

Write-Host "Gerando executável (modo pasta)..." -ForegroundColor Yellow

pyinstaller `
  --noconfirm `
  --clean `
  --name "LeitorCodigos" `
  --windowed `
  --add-data "assets;assets" `
  --add-data "data/equipamentos_template.db;data/equipamentos_template.db" `
  --hidden-import PIL._tkinter_finder `
  --hidden-import PIL.ImageTk `
  --collect-all PIL `
  main.py

Write-Host ">>> BUILD CONCLUÍDO!" -ForegroundColor Green
Write-Host "Pasta final: dist\LeitorCodigos" -ForegroundColor Green
