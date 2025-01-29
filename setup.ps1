# Verifica se o venv já existe
if (-not (Test-Path ".\venv")) {
    Write-Host "Criando ambiente virtual..." -ForegroundColor Green
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Erro ao criar ambiente virtual!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Ambiente virtual já existe." -ForegroundColor Yellow
}

# Ativa o ambiente virtual
Write-Host "Ativando ambiente virtual..." -ForegroundColor Green
try {
    .\venv\Scripts\Activate.ps1
} catch {
    Write-Host "Erro ao ativar ambiente virtual!" -ForegroundColor Red
    exit 1
}

# Verifica se os arquivos de requisitos existem
if (-not (Test-Path "requirements.txt")) {
    Write-Host "Arquivo requirements.txt não encontrado!" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "test-requirements.txt")) {
    Write-Host "Arquivo test-requirements.txt não encontrado!" -ForegroundColor Red
    exit 1
}

# Atualiza pip usando o python do venv
Write-Host "Atualizando pip..." -ForegroundColor Green
& .\venv\Scripts\python.exe -m pip install --upgrade pip

# Instala as dependências usando o python do venv
Write-Host "Instalando dependências..." -ForegroundColor Green
& .\venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro ao instalar dependências!" -ForegroundColor Red
    exit 1
}

# Instala as dependências de teste usando o python do venv
Write-Host "Instalando dependências de teste..." -ForegroundColor Green
& .\venv\Scripts\python.exe -m pip install -r test-requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro ao instalar dependências de teste!" -ForegroundColor Red
    exit 1
}

Write-Host "`nAmbiente configurado com sucesso!" -ForegroundColor Green
Write-Host "Para iniciar a API, execute: python main.py" -ForegroundColor Cyan