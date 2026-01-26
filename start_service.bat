@echo off
setlocal enabledelayedexpansion

:: Simple launcher for Estate AI (Windows)
:: Usage: start_service.bat [api|worker|both]

set MODE=%1
if "%MODE%"=="" set MODE=worker

if "%MODE%"=="-h" goto :usage
if "%MODE%"=="--help" goto :usage
if not "%MODE%"=="api" if not "%MODE%"=="worker" if not "%MODE%"=="both" (
  echo Unknown mode: %MODE%
  goto :usage
)

set ROOT_DIR=%~dp0
set PYTHON_BIN=%PYTHON_BIN%
if "%PYTHON_BIN%"=="" set PYTHON_BIN=%ROOT_DIR%\.venv\Scripts\python.exe

if not exist "%PYTHON_BIN%" (
  echo Python interpreter not found at %PYTHON_BIN%
  exit /b 1
)

if "%MODE%"=="api" goto :start_api
if "%MODE%"=="worker" goto :start_worker
if "%MODE%"=="both" goto :start_both

goto :eof

:start_api
echo Starting API server...
"%PYTHON_BIN%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
exit /b %ERRORLEVEL%

:start_worker
echo Starting worker...
"%PYTHON_BIN%" -m app.worker
exit /b %ERRORLEVEL%

:start_both
echo Starting worker in background...
start "worker" /b "%PYTHON_BIN%" -m app.worker
echo Starting API server in foreground...
"%PYTHON_BIN%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
exit /b %ERRORLEVEL%

:usage
echo Usage: start_service.bat [api^|worker^|both]
echo   api     Start FastAPI server (uvicorn app.main:app)
echo   worker  Start background worker (app.worker)
echo   both    Run worker in background, then API in foreground
echo.
echo Environment variables:
echo   PYTHON_BIN   Override python path (default: .venv\Scripts\python.exe)
exit /b 1
