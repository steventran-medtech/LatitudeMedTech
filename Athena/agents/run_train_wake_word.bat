@echo off
cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\voice
call venv\Scripts\activate
cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\agents
echo Latitude MedTech Wake Word Trainer
echo ------------------------------------
python train_wake_word.py %*
pause
