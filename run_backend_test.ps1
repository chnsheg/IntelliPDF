# 安全运行后端测试 - 在新窗口打开
Write-Host "="*70 -ForegroundColor Cyan
Write-Host "🧪 启动后端 API 测试" -ForegroundColor Cyan
Write-Host "="*70 -ForegroundColor Cyan
Write-Host ""
Write-Host "测试将在新窗口运行，不会中断后端服务" -ForegroundColor Yellow
Write-Host ""

# 在新窗口运行测试
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd D:\IntelliPDF; python test_backend_api.py; Write-Host ''; Write-Host '按任意键关闭窗口...' -ForegroundColor Yellow; `$null = `$Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')"
) -Wait:$false

Write-Host "✅ 测试已在新窗口启动" -ForegroundColor Green
Write-Host "请查看新窗口的测试结果" -ForegroundColor Yellow
Write-Host ""
