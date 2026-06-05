@echo off
echo Latitude MedTech — Deep Historical Knowledge Scraper
echo ======================================================
echo MedTech M^&A + Post-Acquisition Recalls 2010-Present
echo.
echo This runs once. Memory prevents re-ingestion on future runs.
echo Estimated time: 10-20 minutes.
echo.
cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\voice
call venv\Scripts\activate
cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\agents
python deep_scrape.py
pause
