Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting MotoMind FastAPI Backend Server (Port 8000)...  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

& ".\venv\Scripts\python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
