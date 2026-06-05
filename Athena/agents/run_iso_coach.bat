@echo off
cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\voice
call venv\Scripts\activate
cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\agents
echo Latitude MedTech ISO 13485 Coach Agent
echo ----------------------------------------
python iso_coach_agent.py
pause
