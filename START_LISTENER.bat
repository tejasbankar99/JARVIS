@echo off
:: JARVIS Background Listener — Auto-start script
:: Waits 15 seconds after boot so audio services are fully ready

timeout /t 15 /nobreak >nul

cd /d "d:\00.Projects\JARVIS"
".venv\Scripts\pythonw.exe" listener.py
