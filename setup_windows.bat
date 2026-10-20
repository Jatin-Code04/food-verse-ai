@echo off
setlocal
cd /d "%~dp0"
echo =====================================
echo FoodVerse AI - First-time setup
echo =====================================
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher was not found. Install Python 3.12 and enable the Python launcher.
  pause
  exit /b 1
)
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js was not found. Install Node.js LTS from https://nodejs.org/ and reopen this window.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" py -3.12 -m venv .venv
if errorlevel 1 goto error
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto error
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
if errorlevel 1 goto error
if not exist "backend\.env" copy "backend\.env.example" "backend\.env" >nul
cd frontend
call npm install
if errorlevel 1 goto error
cd ..
echo.
echo Setup complete. Edit backend\.env to add your optional Groq API key.
echo Double-click Start Backend.bat and Start Frontend.bat in separate windows.
pause
exit /b 0
:error
echo.
echo Setup stopped because a command failed. Read the error above, then ask for help with a screenshot.
pause
exit /b 1
