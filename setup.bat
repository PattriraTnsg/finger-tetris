@echo off
:: setup.bat — Windows one-click setup for Finger Control Tetris
:: ใช้ครั้งแรกครั้งเดียว แล้วใช้ run.bat เพื่อ run ครั้งต่อไป

echo.
echo ==========================================
echo  Finger Control Tetris — Setup (Windows)
echo ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] ไม่พบ Python กรุณาติดตั้ง Python 3.10+ ก่อน
    echo         https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] สร้าง virtual environment...
python -m venv venv

echo [2/3] Activate venv...
call venv\Scripts\activate.bat

echo [3/3] ติดตั้ง dependencies...
pip install -r requirements.txt

echo.
echo ==========================================
echo  Setup เสร็จแล้ว!
echo  รัน:  python src/main.py
echo  หรือ double-click:  run.bat
echo ==========================================
pause