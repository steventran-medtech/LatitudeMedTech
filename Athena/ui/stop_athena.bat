@echo off
chcp 65001 >nul
echo Stopping Athena...
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "C:\Users\huann\LatitudeMedTech\Athena\ui\stop_athena.ps1"
echo Done.
