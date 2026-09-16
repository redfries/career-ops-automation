@echo off
cd /d "C:\Users\lords\OneDrive\Documents\career-ops-automation"
echo [CareerOps] Launching browser engine at %TIME%...
"C:\Users\lords\AppData\Local\Programs\Python\Python312\python.exe" scripts/browser_apply_engine.py --job-id 4460970498 --mode dry-run --timeout 45
echo [CareerOps] Engine finished with exit code %ERRORLEVEL% at %TIME%
echo. 
pause
