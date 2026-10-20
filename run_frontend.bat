@echo off
echo ==========================================================
echo Starting MotoMind React + Vite Frontend (Port 5173)...
echo ==========================================================
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
