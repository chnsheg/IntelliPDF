# 在新窗口运行测试脚本，不打断后端服务

Write-Host "启动 AI 聊天测试..." -ForegroundColor Cyan
Write-Host "测试将在新窗口运行，不会中断后端服务" -ForegroundColor Yellow

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\IntelliPDF; python test_chat_detailed.py"

Write-Host "`n✅ 测试已在新窗口启动" -ForegroundColor Green
Write-Host "请查看新窗口的测试结果" -ForegroundColor Yellow
