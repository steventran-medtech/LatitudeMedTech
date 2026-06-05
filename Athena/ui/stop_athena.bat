@echo off
chcp 65001 >nul
echo Stopping Athena...
del /F /Q "C:\Users\huann\LatitudeMedTech\Athena\ui\.athena_ready" >nul 2>&1
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe   /T >nul 2>&1
taskkill /F /IM electron.exe /T >nul 2>&1
echo Done.
