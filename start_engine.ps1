# Career-Ops Autonomous HITL Job Application Engine
$Host.UI.RawUI.WindowTitle = "Career-Ops Autonomous HITL Job Application Engine"
Set-Location -Path $PSScriptRoot
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "Starting Career-Ops Autonomous Job Application Engine Cockpit..." -ForegroundColor Cyan
Write-Host "===============================================================================" -ForegroundColor Cyan

python start_engine.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n[ERROR] Engine exited with error code $LASTEXITCODE" -ForegroundColor Red
    Read-Host "Press [Enter] to exit"
}
