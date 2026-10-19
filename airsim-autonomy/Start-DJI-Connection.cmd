@echo off
cd /d "%~dp0"
"%~dp0.venv\Scripts\python.exe" "%~dp0dji_console.py"
if errorlevel 1 pause
