@echo off
:: ============================================================
:: Latitude MedTech — Schedule Weekly Content Draft
:: Runs content_agent.py every Monday at 6:00 AM
:: Run this once as Administrator to set it up
:: ============================================================

echo Latitude MedTech — Scheduling Weekly Content Draft
echo =====================================================
echo.

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Please right-click and select "Run as Administrator"
    pause
    exit /b 1
)

schtasks /create /tn "LatitudeMedTech_Content_Draft" ^
    /tr "cmd /c cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\voice && venv\Scripts\activate && cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\agents && python content_agent.py >> C:\\Users\\huann\\LatitudeMedTech\\Athena\logs\content_scheduled.log 2>&1" ^
    /sc WEEKLY ^
    /d MON ^
    /st 06:00 ^
    /ru "%USERNAME%" ^
    /f

if %errorLevel% equ 0 (
    echo.
    echo SUCCESS: Content draft scheduled for every Monday at 6:00 AM.
    echo Draft will appear in: C:\\Users\\huann\\LatitudeMedTech\\Athena\content\drafts\
    echo.
    echo To run manually now: schtasks /run /tn "LatitudeMedTech_Content_Draft"
    echo To remove: schtasks /delete /tn "LatitudeMedTech_Content_Draft" /f
) else (
    echo ERROR: Could not create scheduled task. Try running as Administrator.
)
echo.
pause
