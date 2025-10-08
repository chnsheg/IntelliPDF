@echo off
REM Test runner script for IntelliPDF
REM Runs tests without interfering with backend server

echo ============================================================
echo Running IntelliPDF Tests
echo ============================================================

cd /d %~dp0

REM Use backend's virtual environment
set PYTHON_EXE=%~dp0backend\venv\Scripts\python.exe

if not exist "%PYTHON_EXE%" (
    echo Error: Python virtual environment not found!
    echo Please run: cd backend ^&^& python -m venv venv
    pause
    exit /b 1
)

REM Run the test
echo.
echo Running bookmark API tests...
echo.
"%PYTHON_EXE%" test_bookmarks.py

echo.
echo ============================================================
echo Tests completed
echo ============================================================
pause
