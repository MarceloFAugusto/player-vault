Write-Host "Procurando por diretórios __pycache__..." -ForegroundColor Yellow

$pycacheDirs = Get-ChildItem -Path "." -Filter "__pycache__" -Directory -Recurse

if ($pycacheDirs.Count -eq 0) {
    Write-Host "Nenhum diretório __pycache__ encontrado." -ForegroundColor Green
    exit
}

Write-Host "Encontrados $($pycacheDirs.Count) diretórios __pycache__." -ForegroundColor Yellow

foreach ($dir in $pycacheDirs) {
    Write-Host "Removendo $($dir.FullName)" -ForegroundColor Cyan
    Remove-Item -Path $dir.FullName -Recurse -Force
}

Write-Host "Limpeza concluída!" -ForegroundColor Green
