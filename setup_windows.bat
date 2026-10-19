@echo off
cd /d "%~dp0"
echo Creating the Python environment. This needs Python 3.12. If it fails, run:  py install 3.12
py -3.12 -m venv .venv
if errorlevel 1 goto fail
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 goto fail
python -m pytest -q tests
if errorlevel 1 goto fail
echo.
echo SETUP OK. The last test line above should say passed and not failed.
echo Next: double-click run_openai.bat
pause
exit /b 0
:fail
echo.
echo Something failed. Copy everything printed above and send it to Claude.
pause
exit /b 1
