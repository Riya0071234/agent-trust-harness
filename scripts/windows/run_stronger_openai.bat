@echo off
cd /d "%~dp0..\.."
call .venv\Scripts\activate.bat
if defined OPENAI_API_KEY goto go
set /p OPENAI_API_KEY=Paste your OpenAI key here and press Enter: 
:go
echo.
echo Step 1 of 2: quick check, 10 games with the stronger OpenAI model. Its data are discarded.
python run.py --smoke --models openai_sol --arms A0,C1,C3,D1,D3 --out results\smoke_openai_sol
if errorlevel 1 goto fail
echo.
echo The quick check passed. Copy the spend line above to Claude if you like, then press any key to start the full run.
pause
echo.
echo Step 2 of 2: 40 games in each of 5 arms (200 games).
python run.py --models openai_sol --arms A0,C1,C3,D1,D3 --out results\stronger_openai_sol --games-per-cell 40
if errorlevel 1 goto fail
echo.
echo If the last line above starts with Finished, the run is complete. Tell Claude: stronger OpenAI done.
pause
exit /b 0
:fail
echo.
echo It stopped. Double-click this file again to resume where it stopped. If it keeps failing, copy the text above to Claude.
pause
exit /b 1
