# 服务状态检查脚本 (不会中断服务器)
# 仅查询服务状态,不发送请求

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "IntelliPDF 服务状态检查" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查后端进程
Write-Host "[1/4] 检查后端进程..." -ForegroundColor Yellow
$backendProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*IntelliPDF*backend*"}
if ($backendProcess) {
    Write-Host "  ✅ 后端进程运行中 (PID: $($backendProcess.Id))" -ForegroundColor Green
    Write-Host "     路径: $($backendProcess.Path)" -ForegroundColor Gray
} else {
    Write-Host "  ❌ 后端进程未找到" -ForegroundColor Red
    Write-Host "     建议: cd backend; .\venv\Scripts\Activate.ps1; python main.py" -ForegroundColor Yellow
}

Write-Host ""

# 检查前端进程
Write-Host "[2/4] 检查前端进程..." -ForegroundColor Yellow
$frontendProcess = Get-Process node -ErrorAction SilentlyContinue | Where-Object {
    $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine
    $cmdLine -like "*vite*" -or $cmdLine -like "*frontend*"
}
if ($frontendProcess) {
    Write-Host "  ✅ 前端进程运行中 (PID: $($frontendProcess.Id))" -ForegroundColor Green
} else {
    Write-Host "  ❌ 前端进程未找到" -ForegroundColor Red
    Write-Host "     建议: cd frontend; npm run dev" -ForegroundColor Yellow
}

Write-Host ""

# 检查端口占用
Write-Host "[3/4] 检查端口占用..." -ForegroundColor Yellow

# 检查 8000 端口 (后端)
$port8000 = netstat -ano | findstr ":8000" | findstr "LISTENING"
if ($port8000) {
    Write-Host "  ✅ 端口 8000 已监听 (后端)" -ForegroundColor Green
    Write-Host "     URL: http://localhost:8000" -ForegroundColor Gray
} else {
    Write-Host "  ❌ 端口 8000 未监听" -ForegroundColor Red
}

# 检查 5174 端口 (前端)
$port5174 = netstat -ano | findstr ":5174" | findstr "LISTENING"
if ($port5174) {
    Write-Host "  ✅ 端口 5174 已监听 (前端)" -ForegroundColor Green
    Write-Host "     URL: http://localhost:5174" -ForegroundColor Gray
} else {
    Write-Host "  ❌ 端口 5174 未监听" -ForegroundColor Red
}

Write-Host ""

# 检查关键文件
Write-Host "[4/4] 检查关键文件..." -ForegroundColor Yellow

$files = @(
    "backend\main.py",
    "backend\venv\Scripts\python.exe",
    "frontend\package.json",
    "frontend\src\pages\DocumentViewerPage.tsx",
    "frontend\src\components\ChatPanel.tsx",
    "frontend\src\components\BookmarkPanel.tsx",
    "frontend\src\components\PDFViewerEnhanced.tsx"
)

$allExists = $true
foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file (缺失)" -ForegroundColor Red
        $allExists = $false
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "检查完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($backendProcess -and $frontendProcess) {
    Write-Host "✅ 系统运行正常!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📍 访问地址:" -ForegroundColor Cyan
    Write-Host "   前端: http://localhost:5174" -ForegroundColor White
    Write-Host "   后端: http://localhost:8000" -ForegroundColor White
    Write-Host "   API文档: http://localhost:8000/api/docs" -ForegroundColor White
    Write-Host ""
    Write-Host "🧪 下一步:" -ForegroundColor Cyan
    Write-Host "   1. 打开浏览器访问 http://localhost:5174" -ForegroundColor White
    Write-Host "   2. 上传测试 PDF" -ForegroundColor White
    Write-Host "   3. 如果页面空白,按 F12 查看 Console 错误" -ForegroundColor White
    Write-Host "   4. 参考文档: PDF_PAGE_BLANK_TROUBLESHOOTING.md" -ForegroundColor White
} else {
    Write-Host "⚠️  部分服务未运行" -ForegroundColor Yellow
    Write-Host ""
    if (-not $backendProcess) {
        Write-Host "启动后端:" -ForegroundColor Yellow
        Write-Host "  cd backend" -ForegroundColor White
        Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
        Write-Host "  python main.py" -ForegroundColor White
        Write-Host ""
    }
    if (-not $frontendProcess) {
        Write-Host "启动前端:" -ForegroundColor Yellow
        Write-Host "  cd frontend" -ForegroundColor White
        Write-Host "  npm run dev" -ForegroundColor White
    }
}

Write-Host ""
