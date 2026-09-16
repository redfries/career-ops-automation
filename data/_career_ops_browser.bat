@echo off
cd /d "C:\Users\lords\OneDrive\Documents\career-ops-automation"
echo ============================================================
echo [CareerOps] Launching browser engine on visible desktop...
echo ============================================================
"C:\Users\lords\AppData\Local\Programs\Python\Python312\python.exe" scripts/browser_apply_engine.py --job-id 4444877183 --mode assisted --timeout 60 2>&1 | powershell -Command "$input | Tee-Object -FilePath 'data\browser_engine.log'"
echo ============================================================
echo [CareerOps] Engine finished with exit code %ERRORLEVEL% at %TIME%
echo ============================================================
timeout /t 10 /nobreak >nul
