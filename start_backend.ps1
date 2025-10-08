# PowerShell script to start backend server in background
# This script starts the server without blocking the terminal

$BackendPath = "d:\IntelliPDF\backend"
$PythonExe = "$BackendPath\venv\Scripts\python.exe"
$MainScript = "$BackendPath\main.py"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Starting IntelliPDF Backend Server" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Check if virtual environment exists
if (-not (Test-Path $PythonExe)) {
    Write-Host "Error: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Path: $PythonExe" -ForegroundColor Red
    exit 1
}

# Kill existing Python processes
Write-Host "`nCleaning existing Python processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Start server in background job
Write-Host "Starting server in background..." -ForegroundColor Yellow
$Job = Start-Job -ScriptBlock {
    param($PythonPath, $ScriptPath, $WorkDir)
    Set-Location $WorkDir
    & $PythonPath $ScriptPath
} -ArgumentList $PythonExe, $MainScript, $BackendPath

# Wait for server to start
Write-Host "Waiting for server to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test if server is running
Write-Host "`nTesting server health..." -ForegroundColor Yellow
$MaxRetries = 5
$RetryCount = 0
$ServerRunning = $false

while ($RetryCount -lt $MaxRetries -and -not $ServerRunning) {
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2
        if ($Response.StatusCode -eq 200) {
            $ServerRunning = $true
            Write-Host "✓ Server is running!" -ForegroundColor Green
            Write-Host "  URL: http://localhost:8000" -ForegroundColor Green
            Write-Host "  Docs: http://localhost:8000/api/docs" -ForegroundColor Green
            Write-Host "  Job ID: $($Job.Id)" -ForegroundColor Cyan
        }
    }
    catch {
        $RetryCount++
        if ($RetryCount -lt $MaxRetries) {
            Write-Host "  Retry $RetryCount/$MaxRetries..." -ForegroundColor Yellow
            Start-Sleep -Seconds 2
        }
    }
}

if (-not $ServerRunning) {
    Write-Host "`n✗ Failed to start server!" -ForegroundColor Red
    Write-Host "Checking job output..." -ForegroundColor Yellow
    Receive-Job -Job $Job
    Remove-Job -Job $Job -Force
    exit 1
}

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "Backend server is ready for testing!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "`nTo stop the server later, run:" -ForegroundColor Yellow
Write-Host "  Get-Job | Stop-Job; Get-Job | Remove-Job" -ForegroundColor White
Write-Host "  or" -ForegroundColor Yellow
Write-Host "  Get-Process python | Stop-Process -Force" -ForegroundColor White
