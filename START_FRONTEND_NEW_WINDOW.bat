@echo off
REM 在新窗口中启动前端,不影响后端服务器
cd /d "%~dp0"
start "IntelliPDF Frontend" cmd /k "cd frontend && npm run dev"
echo 前端已在新窗口中启动
echo 窗口标题: IntelliPDF Frontend
timeout /t 3
