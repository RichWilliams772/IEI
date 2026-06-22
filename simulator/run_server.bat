@echo off
echo Starting Electrical Diagram Simulator...
cd /d "%~dp0"
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies
    pause
    exit /b %errorlevel%
)
echo Starting server...
cd /d "%~dp0.."
python -m uvicorn simulator.backend.api:app --host 0.0.0.0 --port 8000
pause
