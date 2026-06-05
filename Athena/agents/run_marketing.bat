@echo off
REM Latitude MedTech — Marketing Agent Launcher
REM Usage: run_marketing.bat [--plan] [--pipeline] [--events] [--scorecard] [--outreach "TARGET"]
cd /d "%~dp0"
call ..\voice\venv\Scripts\activate.bat 2>nul || call ..\venv\Scripts\activate.bat 2>nul
python marketing_agent.py %*
pause
