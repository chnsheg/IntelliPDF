@echo off
echo ========================================
echo PDF 空白页面问题 - 快速修复
echo ========================================
echo.
echo 问题: Vite 配置缺少 API 代理
echo 解决: 已添加代理配置到 vite.config.ts
echo 操作: 重启前端应用修复
echo.
echo ========================================
echo.

cd /d "%~dp0frontend"

echo [1/3] 停止现有前端进程...
taskkill /F /IM node.exe 2>nul
if %errorlevel% equ 0 (
    echo       已停止 Node 进程
) else (
    echo       没有运行中的 Node 进程
)
timeout /t 2 /nobreak >nul

echo.
echo [2/3] 清除 Vite 缓存...
if exist "node_modules\.vite" (
    rmdir /s /q "node_modules\.vite"
    echo       Vite 缓存已清除
) else (
    echo       Vite 缓存不存在
)

echo.
echo [3/3] 启动前端服务器 (应用代理配置)...
echo.
echo ========================================
echo 前端将在 http://localhost:5174 运行
echo 后端代理到 http://localhost:8000
echo ========================================
echo.
echo 修复说明:
echo   - 添加了 /api 路径代理配置
echo   - 前端请求将自动转发到后端
echo   - PDF 详情页面应该正常显示
echo.
echo 测试步骤:
echo   1. 等待前端启动完成
echo   2. 访问 http://localhost:5174
echo   3. 点击 PDF 查看详情
echo   4. 页面应该显示 PDF 内容 (不再空白)
echo.
echo ========================================
echo.

call npm run dev
