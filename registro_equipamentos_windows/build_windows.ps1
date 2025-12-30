# ===============================
# Build Windows - Registro de Equipamentos
# ===============================

Write-Host ">>> Build Windows - Registro de Equipamentos" -ForegroundColor Cyan

# 1) Ativar venv
if (!(Test-Path ".\.venv")) {
    Write-Host "Criando ambiente virtual..." -ForegroundColor Yellow
    python -m venv .venv
}

Write-Host "Ativando venv..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1

# 2) Atualizar pip
python -m pip install --upgrade pip

# 3) Instalar dependências
Write-Host "Instalando dependências..." -ForegroundColor Yellow
pip install -r requirements.txt
pip install pyinstaller

# 4) Limpar builds antigos
if (Test-Path "build") { Remove-Item -Recurse -Force build }
if (Test-Path "dist")  { Remove-Item -Recurse -Force dist }

# 5) Executar PyInstaller (modo pasta / mais confiável)
Write-Host "Gerando executável (modo pasta)..." -ForegroundColor Yellow

pyinstaller `
  --noconfirm `
  --clean `
  --name "RegistroEquipamentos" `
  --windowed `
  --add-data "assets;assets" `
  --add-data "equipamentos.db;equipamentos.db" `
  --hidden-import PIL._tkinter_finder `
  --hidden-import PIL.ImageTk `
  --collect-all PIL `
  main.py

Write-Host ">>> BUILD CONCLUÍDO COM SUCESSO!" -ForegroundColor Green
Write-Host "Pasta final: dist\RegistroEquipamentos" -ForegroundColor Green
