@echo off
:: ============================================================
:: Latitude MedTech — Schedule Daily Morning Briefing
:: Runs briefing_agent.py every morning at 7:00 AM
:: Run this once as Administrator
:: ============================================================

echo Latitude MedTech — Scheduling Daily Briefing
echo =============================================
echo.

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Please right-click and select "Run as Administrator"
    pause
    exit /b 1
)

schtasks /create /tn "LatitudeMedTech_Daily_Briefing" ^
    /tr "cmd /c cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\voice && venv\Scripts\activate && cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\agents && python briefing_agent.py >> C:\\Users\\huann\\LatitudeMedTech\\Athena\logs\briefing_scheduled.log 2>&1" ^
    /sc DAILY ^
    /st 07:00 ^
    /ru "%USERNAME%" ^
    /f

if %errorLevel% equ 0 (
    echo.
    echo SUCCESS: Daily briefing scheduled for 7:00 AM every morning.
    echo Briefings will appear in: C:\\Users\\huann\\LatitudeMedTech\\Athena\briefings\
    echo.
    echo To run manually: schtasks /run /tn "LatitudeMedTech_Daily_Briefing"
    echo To remove:       schtasks /delete /tn "LatitudeMedTech_Daily_Briefing" /f
) else (
    echo ERROR: Could not create task. Try running as Administrator.
)
echo.
pause
