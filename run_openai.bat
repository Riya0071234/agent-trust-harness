@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
if defined OPENAI_API_KEY goto go
set /p OPENAI_API_KEY=Paste your OpenAI key here and press Enter: 
:go
python run.py --models openai --out results\openai --games-per-cell 160
echo.
echo If the last line above starts with Finished, the run is complete.
echo If it stopped early, double-click this file again. It resumes where it stopped.
pause
