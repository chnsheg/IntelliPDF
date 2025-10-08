@echo off
TITLE IntelliPDF Frontend Dev Server
cd /d %~dp0frontend
echo ============================================
echo Starting IntelliPDF Frontend Dev Server
echo ============================================
echo.
echo Starting Vite dev server...
echo Frontend will be available at http://localhost:5173
echo.
npm run dev
pause
