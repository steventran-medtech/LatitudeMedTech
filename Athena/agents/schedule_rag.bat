@echo off
:: ============================================================
:: Latitude MedTech — Schedule Nightly RAG Ingestion
:: Runs rag_agent.py every night at 2:00 AM automatically
:: Run this once as Administrator to set it up
:: ============================================================

echo Latitude MedTech — Scheduling Nightly RAG Ingestion
echo =====================================================
echo.

:: Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Please right-click this file and select "Run as Administrator"
    pause
    exit /b 1
)

:: Create the task
schtasks /create /tn "LatitudeMedTech_RAG_Ingestion" ^
    /tr "cmd /c cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\voice && venv\Scripts\activate && cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\agents && python rag_agent.py >> C:\\Users\\huann\\LatitudeMedTech\\Athena\logs\rag_scheduled.log 2>&1" ^
    /sc DAILY ^
    /st 02:00 ^
    /ru "%USERNAME%" ^
    /f

if %errorLevel% equ 0 (
    echo.
    echo SUCCESS: RAG ingestion scheduled for 2:00 AM nightly.
    echo.
    echo To verify: open Task Scheduler and look for "LatitudeMedTech_RAG_Ingestion"
    echo To run manually now: schtasks /run /tn "LatitudeMedTech_RAG_Ingestion"
    echo To remove: schtasks /delete /tn "LatitudeMedTech_RAG_Ingestion" /f
) else (
    echo.
    echo ERROR: Could not create scheduled task. Try running as Administrator.
)
echo.
pause
