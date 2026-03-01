@echo off
:: Заставляем скрипт ПРИНУДИТЕЛЬНО перейти в папку, где он лежит
cd /d "%~dp0"

timeout /t 5
taskkill /f /im python.exe >nul 2>&1
call venv\Scripts\activate
python main.py
pause