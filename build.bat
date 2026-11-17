@echo off
REM Cree dist\LyricVideoMaker.exe (necessite Python 3.10+ installe sur Windows)
cd /d "%~dp0"
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --onefile --windowed --name LyricVideoMaker ^
  --add-data "fonts;fonts" --collect-all imageio_ffmpeg app.py
echo.
echo Termine : dist\LyricVideoMaker.exe
pause
