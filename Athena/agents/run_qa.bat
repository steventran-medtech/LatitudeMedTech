@echo off
echo Latitude MedTech QA Test Suite
echo ================================
echo.
cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\voice
call venv\Scripts\activate
cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\agents
python qa_test.py %*
pause
