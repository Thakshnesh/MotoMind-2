Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting MotoMind React + Vite Frontend (Port 5173)...  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

Set-Location -Path "frontend"
npm run dev -- --host 127.0.0.1 --port 5173
