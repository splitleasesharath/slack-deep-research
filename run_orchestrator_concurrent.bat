@echo off
REM Deep Research Orchestrator - Concurrent Version
REM Supports multiple instances running every 3 minutes

echo =========================================
echo    CONCURRENT ORCHESTRATOR
echo    Session Starting
echo =========================================
echo.
echo This version supports concurrent execution
echo Multiple instances can run simultaneously
echo Each session has a unique ID for tracking
echo.
echo =========================================
echo.

REM Navigate to script directory
cd /d "%~dp0"

REM Install filelock if needed (first run only)
python -m pip install filelock >nul 2>&1

REM Run the concurrent orchestrator
python orchestrator_concurrent.py

REM Exit with Python's exit code
exit /b %ERRORLEVEL%