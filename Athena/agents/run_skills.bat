@echo off
cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\voice
call venv\Scripts\activate
cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\agents
echo Latitude MedTech - Skills/KB Profile Generation
echo ------------------------------------------------
python skills_profile.py %*
pause
