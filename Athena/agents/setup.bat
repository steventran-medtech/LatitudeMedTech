@echo off
echo Setting up Latitude MedTech agent workspace...

mkdir C:\\Users\\huann\\LatitudeMedTech\\Athena\knowledge_base 2>nul
mkdir C:\\Users\\huann\\LatitudeMedTech\\Athena\content\drafts 2>nul
mkdir C:\\Users\\huann\\LatitudeMedTech\\Athena\content\published 2>nul
mkdir C:\\Users\\huann\\LatitudeMedTech\\Athena\coaching\briefs 2>nul
mkdir C:\\Users\\huann\\LatitudeMedTech\\Athena\logs 2>nul

echo.
echo Folders created:
echo   C:\\Users\\huann\\LatitudeMedTech\\Athena\knowledge_base\
echo   C:\\Users\\huann\\LatitudeMedTech\\Athena\content\drafts\
echo   C:\\Users\\huann\\LatitudeMedTech\\Athena\content\published\
echo   C:\\Users\\huann\\LatitudeMedTech\\Athena\coaching\briefs\
echo   C:\\Users\\huann\\LatitudeMedTech\\Athena\logs\
echo.
echo Installing Python dependencies...

cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\voice
call venv\Scripts\activate
pip install anthropic beautifulsoup4 requests python-dotenv feedparser schedule -q

echo.
echo Setup complete. You are ready to run the agents.
pause
