@echo off
REM Simple startup without migrations

cd /d %~dp0

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting server...
python main.py

pause
