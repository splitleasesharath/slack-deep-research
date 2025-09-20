@echo off
REM Deep Research Orchestrator - Fully Automatic
REM Runs the complete workflow including 20-minute scheduled report retrieval

echo =========================================
echo    DEEP RESEARCH ORCHESTRATOR
echo    Automatic Execution Starting
echo =========================================
echo.
echo The process will:
echo 1. Retrieve Slack messages
echo 2. Process oldest unprocessed message
echo 3. Generate deep research
echo 4. Wait 20 minutes for report generation
echo 5. Retrieve and send report to Slack
echo 6. Exit automatically when complete
echo.
echo =========================================
echo.

REM Navigate to script directory
cd /d "%~dp0"

REM Run the orchestrator
python orchestrator.py

REM Show completion message
if %ERRORLEVEL% EQU 0 (
    echo.
    echo =========================================
    echo Process completed successfully
    echo =========================================
) else (
    echo.
    echo =========================================
    echo Process failed with error code: %ERRORLEVEL%
    echo Check orchestrator.log for details
    echo =========================================
)

REM Exit with the Python script's exit code
exit /b %ERRORLEVEL%