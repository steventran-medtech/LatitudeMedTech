@echo off
cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\voice
call venv\Scripts\activate
cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\agents
echo Latitude MedTech Coaching Brief Agent
echo ----------------------------------------
set /p CLIENT="Enter client name or LinkedIn URL: "
python coaching_brief.py "%CLIENT%"
pause
