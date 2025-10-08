@echo off
REM 前端重启脚本 - 清除缓存并重新编译

echo ========================================
echo 清除前端缓存并重启
echo ========================================

cd /d "%~dp0frontend"

echo.
echo [1/4] 停止现有进程...
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [2/4] 清除 Vite 缓存...
if exist "node_modules\.vite" (
    rmdir /s /q "node_modules\.vite"
    echo Vite 缓存已清除
) else (
    echo Vite 缓存不存在
)

echo.
echo [3/4] 清除 TypeScript 缓存...
if exist ".tsbuildinfo" (
    del /f /q ".tsbuildinfo"
    echo TypeScript 缓存已清除
)

echo.
echo [4/4] 启动开发服务器...
echo 前端将在 http://localhost:5174 运行
echo.

call npm run dev
