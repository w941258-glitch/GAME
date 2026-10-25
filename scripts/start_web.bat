@echo off
setlocal
cd /d "%~dp0.."
where py >nul 2>nul
if errorlevel 1 (
  echo Please install Python 3.12 from python.org, then run this file again.
  pause
  exit /b 1
)
if not exist .venv\Scripts\python.exe (
  py -3.12 -m venv .venv
  if errorlevel 1 goto :failed
)
.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
if errorlevel 1 goto :failed
echo Open your browser and enter 127.0.0.1:8000 after startup completes.
echo Keep this window open while playing. Press Ctrl+C to stop.
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
exit /b %errorlevel%
:failed
echo Setup failed. Check Python 3.12 and your network connection.
pause
exit /b 1
