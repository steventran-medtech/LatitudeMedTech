@echo off
cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\voice
call venv\Scripts\activate
cd /d C:\\Users\\huann\\LatitudeMedTech\\Athena\agents
echo Latitude MedTech — 15-Minute Knowledge Scrape
echo ================================================
echo Running RAG ingestion for 15 minutes...
echo Outputs: C:\\Users\\huann\\LatitudeMedTech\\Athena\knowledge_base\
echo.
timeout /t 2 /nobreak >nul
python rag_agent.py
echo.
echo Done. Knowledge base updated.
pause
