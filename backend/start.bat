@echo off
REM IntelliPDF Backend Startup Script for Windows

echo ========================================
echo IntelliPDF Backend Startup
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run: .\venv\Scripts\activate
    echo Then run: pip install -r requirements\dev.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/4] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo Copying .env.example to .env...
    copy .env.example .env
    echo.
    echo [ACTION REQUIRED] Please edit .env file with your configuration:
    echo - DATABASE_URL
    echo - OPENAI_API_KEY
    echo - SECRET_KEY
    echo.
    echo Press any key to open .env in notepad...
    pause
    notepad .env
)

REM Check database connection
echo [2/4] Checking database connection...
python -c "from app.core.config import get_settings; settings = get_settings(); print(f'Database: {settings.database_url}')" 2>nul
if errorlevel 1 (
    echo [ERROR] Configuration error! Please check your .env file.
    pause
    exit /b 1
)

REM Run database migrations
echo [3/4] Running database migrations...
alembic upgrade head
if errorlevel 1 (
    echo [ERROR] Database migration failed!
    echo Please check:
    echo - PostgreSQL is running
    echo - Database exists
    echo - DATABASE_URL is correct
    pause
    exit /b 1
)

REM Start server
echo [4/4] Starting IntelliPDF server...
echo.
echo ========================================
echo Server starting on http://localhost:8000
echo API Documentation: http://localhost:8000/api/docs
echo ========================================
echo.
echo Press Ctrl+C to stop the server
echo.

python main.py

pause
