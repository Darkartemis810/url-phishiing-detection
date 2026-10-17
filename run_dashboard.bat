@echo off
echo ===================================================
echo Starting URL Phishing Intelligence Web Dashboard...
echo ===================================================
echo.
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)
python app_web.py
pause
