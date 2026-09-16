"""
Interactive Browser Launcher for Career-Ops.

Solves Windows Session 0 Isolation: when an AI agent runs commands, 
GUI windows are invisible because they launch in a background session.
This launcher uses Windows Scheduled Tasks with the /IT (interactive) flag 
to run browser commands in the USER's desktop session — making Brave visible.

Usage (called by the agent):
    python scripts/interactive_launch.py --job-id 4460970498 --mode dry-run
    python scripts/interactive_launch.py --job-id 4460970498 --mode assisted
    python scripts/interactive_launch.py --apply 3 --mode assisted
"""
import os
import sys
import time
import argparse
import subprocess
import datetime

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PYTHON_EXE = sys.executable
TASK_NAME = "CareerOps_BrowserApply"
LOG_FILE = os.path.join(REPO_DIR, 'data', 'interactive_launch.log')


def create_batch_wrapper(cmd_args: list[str]) -> str:
    """Create a .bat wrapper that sets the working directory and runs the command."""
    bat_path = os.path.join(REPO_DIR, 'data', '_career_ops_browser.bat')
    
    # Build the command line
    quoted_python = f'"{PYTHON_EXE}"'
    quoted_args = ' '.join(f'"{a}"' if ' ' in a else a for a in cmd_args)
    
    bat_content = f"""@echo off
cd /d "{REPO_DIR}"
echo [CareerOps] Launching browser engine at %TIME%...
{quoted_python} {quoted_args}
echo [CareerOps] Engine finished with exit code %ERRORLEVEL% at %TIME%
echo. 
pause
"""
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    
    return bat_path


def launch_interactive(bat_path: str) -> bool:
    """Register and immediately run a Windows Scheduled Task in the interactive session."""
    username = os.environ.get('USERNAME', os.environ.get('USER', ''))
    
    # Delete old task if exists (ignore errors)
    subprocess.run(
        ['schtasks', '/delete', '/tn', TASK_NAME, '/f'],
        capture_output=True, text=True
    )
    
    # Create task: /IT = interactive (user's desktop), /RL HIGHEST = elevated if needed
    # /RU with current username ensures it runs in the logged-on user's session
    create_cmd = [
        'schtasks', '/create',
        '/tn', TASK_NAME,
        '/tr', f'"{bat_path}"',
        '/sc', 'once',
        '/st', '00:00',        # Dummy time (we trigger manually)
        '/sd', '01/01/2000',   # Dummy date (we trigger manually)  
        '/IT',                  # Interactive — runs on user's desktop!
        '/F',                   # Force overwrite
    ]
    
    result = subprocess.run(create_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] Failed to create scheduled task: {result.stderr}")
        return False
    
    print(f"[OK] Scheduled task '{TASK_NAME}' created.")
    
    # Run it immediately
    run_result = subprocess.run(
        ['schtasks', '/run', '/tn', TASK_NAME],
        capture_output=True, text=True
    )
    
    if run_result.returncode != 0:
        print(f"[ERROR] Failed to run task: {run_result.stderr}")
        return False
    
    print(f"[OK] Task launched in your interactive desktop session!")
    print(f"     Brave should be VISIBLE on your screen now.")
    
    # Poll task status until it completes
    print(f"\n[Monitoring] Waiting for browser engine to finish...")
    while True:
        time.sleep(3)
        status = subprocess.run(
            ['schtasks', '/query', '/tn', TASK_NAME, '/fo', 'CSV', '/nh'],
            capture_output=True, text=True
        )
        output = status.stdout.strip()
        if 'Running' in output:
            sys.stdout.write('.')
            sys.stdout.flush()
        else:
            print(f"\n[DONE] Browser engine task completed.")
            break
    
    # Cleanup: delete the task
    subprocess.run(['schtasks', '/delete', '/tn', TASK_NAME, '/f'], capture_output=True)
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Interactive Browser Launcher (visible on user's screen)")
    parser.add_argument('--job-id', type=str, help='Job ID to apply to')
    parser.add_argument('--mode', type=str, choices=['assisted', 'dry-run', 'auto'], default='assisted')
    parser.add_argument('--timeout', type=int, default=45, help='Mediator timeout')
    parser.add_argument('--apply', type=int, help='Batch apply N jobs (uses run_batch.py)')
    parser.add_argument('--tailor', type=int, help='Batch tailor N jobs (uses run_batch.py)')
    args = parser.parse_args()
    
    # Build the underlying command
    if args.apply:
        cmd_args = ['scripts/run_batch.py', '--apply', str(args.apply), '--mode', args.mode]
    elif args.tailor:
        cmd_args = ['scripts/run_batch.py', '--tailor', str(args.tailor)]
    elif args.job_id:
        cmd_args = ['scripts/browser_apply_engine.py', '--job-id', args.job_id, '--mode', args.mode, '--timeout', str(args.timeout)]
    else:
        print("Error: Specify --job-id, --apply, or --tailor")
        sys.exit(1)
    
    print("=" * 60)
    print("CAREER-OPS INTERACTIVE BROWSER LAUNCHER")
    print("=" * 60)
    print(f"Command: python {' '.join(cmd_args)}")
    print(f"Mode:    {args.mode}")
    print(f"Method:  Windows Scheduled Task (/IT interactive)")
    print("=" * 60)
    
    bat_path = create_batch_wrapper(cmd_args)
    print(f"[OK] Batch wrapper: {bat_path}")
    
    success = launch_interactive(bat_path)
    
    if success:
        print("\n Browser session completed. Check the database for updated status.")
    else:
        print("\n[FALLBACK] Run this command in your own PowerShell terminal:")
        print(f"  cd {REPO_DIR}")
        print(f"  python {' '.join(cmd_args)}")


if __name__ == '__main__':
    main()
