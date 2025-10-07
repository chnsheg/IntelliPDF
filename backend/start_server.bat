@echo off
cd /d d:\IntelliPDF\backend
echo Starting IntelliPDF Backend Server...
echo Server will run on http://0.0.0.0:8000
echo Press Ctrl+C to stop the server
echo.
d:\IntelliPDF\backend\venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000
