@echo off
cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\voice
call venv\Scripts\activate
cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\agents
echo Latitude MedTech Daily Briefing
echo ---------------------------------
python briefing_agent.py
pause
