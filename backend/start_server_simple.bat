@echo off
REM Start IntelliPDF Backend Server
echo Starting IntelliPDF Backend Server...

cd /d %~dp0

REM Activate virtual environment and start server
call venv\Scripts\activate.bat
python main.py
