@echo off
cd /d "%~dp0..\.."
call .venv\Scripts\activate.bat
if defined ANTHROPIC_API_KEY goto key2
set /p ANTHROPIC_API_KEY=Paste your Anthropic (Claude) key here and press Enter: 
:key2
if defined OPENAI_API_KEY goto go
set /p OPENAI_API_KEY=Paste your OpenAI key here and press Enter: 
:go
echo.
echo Step 1 of 3: quick check, 18 games. Its data are discarded.
python run.py --smoke --pair "claude>openai" --out results\smoke_cross
if errorlevel 1 goto fail
echo.
echo Step 2 of 3: Claude buys from an OpenAI supplier, 1440 games.
python run.py --pair "claude>openai" --out results\cross_claude_buys --games-per-cell 160 --max-spend 0.9
if errorlevel 1 goto fail
echo.
echo Step 3 of 3: OpenAI buys from a Claude supplier, 1440 games.
python run.py --pair "openai>claude" --out results\cross_openai_buys --games-per-cell 160 --max-spend 0.9
if errorlevel 1 goto fail
echo.
echo Both runs finished if you saw two lines starting with Finished. Tell Claude: cross-vendor done.
pause
exit /b 0
:fail
echo.
echo It stopped. Double-click this file again to resume where it stopped. If it keeps failing, copy the text above to Claude.
pause
exit /b 1
