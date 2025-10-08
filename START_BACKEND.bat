@echo off
TITLE IntelliPDF Backend Server
cd /d %~dp0backend
echo ============================================
echo Starting IntelliPDF Backend Server
echo ============================================
echo.
call venv\Scripts\activate.bat
echo Virtual environment activated
echo.
echo Starting server on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
python main.py
pause
