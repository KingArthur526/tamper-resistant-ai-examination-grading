@echo off
echo Starting Tamper-Resistant Examination Grading System...
echo ========================================================

start "Grading Backend" cmd /k "cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
timeout /t 3 /nobreak >nul

start "Grading Frontend" cmd /k "cd frontend && npm run dev"
echo Backend running on http://127.0.0.1:8000
echo Frontend running on http://localhost:5173
echo ========================================================
