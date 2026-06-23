@echo off
echo ===================================================
echo     Production AI Data Visualization System
echo ===================================================

cd %~dp0

:: Check for .env file
IF NOT EXIST "backend\.env" (
    echo [WARNING] backend\.env not found! Creating from .env.example...
    copy .env.example backend\.env
)

echo.
echo [1/3] Setting up and Starting FastAPI Backend...
cd backend
IF NOT EXIST "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo Installing backend requirements...
pip install -r requirements.txt >nul
start "Backend Server" cmd /k "call venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo.
echo [2/3] Setting up and Starting React Frontend...
cd ..\frontend
echo Installing frontend dependencies...
call npm install >nul
start "Frontend Server" cmd /k "npm run dev"

echo.
echo [3/3] Opening Browser...
timeout /t 5 /nobreak >nul
start http://localhost:5173

echo ===================================================
echo   System is running!
echo   Close this window to stop. The spawned terminal windows must be closed to stop servers.
echo ===================================================
pause
