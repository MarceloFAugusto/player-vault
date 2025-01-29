Write-Host "Verificando ambiente e instalando dependências..." -ForegroundColor Green

# Verifica se o pip está instalado
if (!(Get-Command pip -ErrorAction SilentlyContinue)) {
    Write-Host "Erro: pip não está instalado." -ForegroundColor Red
    exit 1
}

# Verifica se o venv já existe
if (-not (Test-Path ".\venv")) {
    Write-Host "Criando ambiente virtual..." -ForegroundColor Green
    python -m venv venv
} else {
    Write-Host "Ambiente virtual já existe." -ForegroundColor Yellow
}

# Ativa o ambiente virtual
Write-Host "Ativando ambiente virtual..." -ForegroundColor Green
.\venv\Scripts\Activate.ps1

# Atualiza pip
Write-Host "Atualizando pip..." -ForegroundColor Green
python -m pip install --upgrade pip

# Instala as dependências do requirements.txt
Write-Host "Instalando dependências do projeto..." -ForegroundColor Yellow
pip install -r requirements.txt

# Garante que todas as dependências necessárias estão instaladas
Write-Host "Verificando dependências adicionais..." -ForegroundColor Yellow
pip install beautifulsoup4 lxml html5lib

# Verifica se pyinstaller foi instalado corretamente
if (!(Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "Instalando PyInstaller..." -ForegroundColor Yellow
    pip install pyinstaller
}

# Adiciona um pequeno delay antes de iniciar o build
Start-Sleep -Seconds 2

# Garante que não há processos anteriores rodando
Get-Process "valorant-ranks" -ErrorAction SilentlyContinue | Stop-Process -Force

# Limpa builds anteriores com tempo de espera
if (Test-Path "dist") {
    Remove-Item -Path "dist" -Recurse -Force
    Start-Sleep -Seconds 1
}
if (Test-Path "build") {
    Remove-Item -Path "build" -Recurse -Force
    Start-Sleep -Seconds 1
}

# Executa o script de minificação
#Write-Host "Minificando arquivos estáticos..." -ForegroundColor Yellow
#python minify.py
#if ($LASTEXITCODE -ne 0) {
#    Write-Host "Erro durante a minificação dos arquivos!" -ForegroundColor Red
#    exit 1
#}

# Gera o executável com configurações ajustadas
Write-Host "Gerando executável..." -ForegroundColor Yellow
pyinstaller --clean `
    --onefile `
    --add-data "static_min/*;static_min/" `
    --add-data "static_min/css/*;static_min/css/" `
    --add-data "static_min/js/*;static_min/js/" `
    --add-data "services/*;services/" `
    --add-data "app.py;." `
    --add-data "*.py;." `
    --add-data ".env.prod;.env" `
    --hidden-import "fastapi" `
    --hidden-import "uvicorn" `
    --hidden-import "python-multipart" `
    --hidden-import "requests" `
    --hidden-import "pyotp" `
    --hidden-import "cryptography" `
    --hidden-import "python-dotenv" `
    --hidden-import "beautifulsoup4" `
    --hidden-import "pydantic" `
    --name "valorant-ranks" `
    --icon "static_min/favicon.ico" `
    --runtime-hook "runtime_hook.py" `
    --hide-console hide-early `
    --log-level DEBUG `
    --workpath "build" `
    run.py

# Aguarda um momento antes de copiar os arquivos
Start-Sleep -Seconds 2

# Verifica se o executável foi gerado corretamente
if (Test-Path "dist\valorant-ranks.exe") {
    Write-Host "`nBuild concluída com sucesso!" -ForegroundColor Green
    Write-Host "`nBuild concluída com sucesso!" -ForegroundColor Green
    Write-Host "O executável foi gerado em: $((Get-Location).Path)\dist\valorant-ranks.exe" -ForegroundColor Cyan

    # Remove a pasta static_min após a build
    if (Test-Path "static_min") {
        Write-Host "Removendo pasta static_min..." -ForegroundColor Yellow
        Remove-Item -Path "static_min" -Recurse -Force
    }
} else {
    Write-Host "`nErro: Executável não foi gerado corretamente!" -ForegroundColor Red
}