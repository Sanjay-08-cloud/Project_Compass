# Launch Project Compass Django Backend & RAG Engine
Write-Host "Starting Project Compass Backend on http://127.0.0.1:8000..." -ForegroundColor Green
Set-Location -Path "$PSScriptRoot"
& "$PSScriptRoot\.venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000
