@echo off
echo Starting URL Phishing Detection Demo...
echo.
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)
python demo_live.py
pause
