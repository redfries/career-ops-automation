@echo off
TITLE Career-Ops Autonomous HITL Job Application Engine
COLOR 0B
cd /d "%~dp0"

echo ===============================================================================
echo Starting Career-Ops Autonomous Job Application Engine Cockpit...
echo ===============================================================================

python start_engine.py
if errorlevel 1 (
    echo.
    echo [ERROR] Engine exited with an error code.
    pause
)
