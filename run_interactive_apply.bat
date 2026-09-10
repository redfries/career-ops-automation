@echo off
TITLE Career-Ops Live Visible Application Runner
COLOR 0A
cd /d "%~dp0"

echo ===============================================================================
echo   CAREER-OPS LIVE VISIBLE APPLICATION RUNNER (INTERACTIVE DESKTOP)
echo ===============================================================================
echo.
echo Launching Playwright in visible headed mode directly on your desktop display...
echo You will see the Chromium browser window pop open right in front of you!
echo If a Cloudflare captcha appears, simply check the box. The automation
echo will detect when it clears, fill the fields, and proceed with your application.
echo.
echo ===============================================================================

python start_engine.py --apply 1

echo.
echo ===============================================================================
echo Run finished. Check above for status and receipt.
echo ===============================================================================
pause
