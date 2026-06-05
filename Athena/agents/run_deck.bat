@echo off
cd /d "%~dp0"
"..\voice\venv\Scripts\python.exe" deck_agent.py %*
