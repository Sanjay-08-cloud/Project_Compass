# Project Compass Consolidated Dev Runner
# One command, one port (8000), internal Ollama, whole stack up.

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Project Compass — Consolidated Single-Port Stack (8000)   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

Set-Location -Path "$PSScriptRoot"

# 1. Check Ollama
Write-Host "[1/3] Verifying Ollama on 127.0.0.1:11434 (Internal-only)..." -ForegroundColor Yellow
$ollamaRunning = $false
try {
    $res = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($res) { $ollamaRunning = $true }
} catch {}

if ($ollamaRunning) {
    Write-Host "  -> Ollama is active on 127.0.0.1:11434." -ForegroundColor Green
} else {
    Write-Host "  -> Starting Ollama service in background..." -ForegroundColor Yellow
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 2
}

# 2. Check / Build frontend static export
Write-Host "[2/3] Verifying frontend static export..." -ForegroundColor Yellow
if (-not (Test-Path "$PSScriptRoot\frontend_build\index.html")) {
    Write-Host "  -> Building frontend static export..." -ForegroundColor Yellow
    Set-Location -Path "$PSScriptRoot\frontend"
    npm.cmd run build
    Set-Location -Path "$PSScriptRoot"
    if (Test-Path "$PSScriptRoot\frontend_build") { Remove-Item -Recurse -Force "$PSScriptRoot\frontend_build" }
    Copy-Item -Recurse -Force "$PSScriptRoot\frontend\out" -Destination "$PSScriptRoot\frontend_build"
}
Write-Host "  -> Frontend build ready in frontend_build/." -ForegroundColor Green

# 3. Run Django Server
Write-Host "[3/3] Starting Django Consolidated Server on http://127.0.0.1:8000..." -ForegroundColor Green
& "$PSScriptRoot\.venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000
