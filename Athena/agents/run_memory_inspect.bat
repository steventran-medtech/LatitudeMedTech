@echo off
cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\voice
call venv\Scripts\activate
cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\agents
echo Athena Memory Inspector
echo -----------------------
python memory_inspect.py %*
pause
