import os
import sys
import json
import time
import sqlite3
import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = 'data/jobs.db'
BRAVE_EXE = os.environ.get(
    'BRAVE_PATH',
    r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe'
)
# Use Brave's own User Data so existing login cookies (LinkedIn, etc.) persist
PROFILE_DIR = os.environ.get(
    'BROWSER_PROFILE_DIR',
    os.path.join(os.environ.get('LOCALAPPDATA', ''), 'BraveSoftware', 'Brave-Browser', 'User Data')
)
os.makedirs(PROFILE_DIR, exist_ok=True)

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def prompt_mediator(company: str, title: str, timeout_sec: int = 45, auto_confirm: bool = False) -> bool:
    """Alerts user with an audible chime and gives a countdown to mediate in the visible browser.
    
    When auto_confirm=True (agent mode), skips the countdown and proceeds immediately.
    Otherwise checks both msvcrt (console) and stdin (pipe) for ENTER input.
    """
    if auto_confirm:
        print("\n[Mediator] Auto-confirm enabled (agent mode). Proceeding immediately...")
        return True

    try:
        sys.stdout.write('\a')
        sys.stdout.flush()
    except Exception:
        pass

    print("\n" + "=" * 65)
    print(f"[MEDIATOR ACTION REQUIRED] - {company} | {title}")
    print("Please review the open Brave window: fill missing fields, sign in, or solve CAPTCHA.")
    print(f"Supervisor countdown: {timeout_sec}s to mediate before skipping cleanly.")
    print("Press [ENTER] in this terminal once ready to proceed (or wait to skip)...")
    print("=" * 65)

    start_time = time.time()
    
    # Check if stdin is a pipe/redirected (agent mode) vs interactive console
    import select
    stdin_is_pipe = not sys.stdin.isatty()
    
    if stdin_is_pipe:
        # Agent mode: read from stdin pipe
        while time.time() - start_time < timeout_sec:
            remaining = int(timeout_sec - (time.time() - start_time))
            sys.stdout.write(f"\r[Mediator Timer] {remaining}s remaining... (waiting for stdin) ")
            sys.stdout.flush()
            
            # Non-blocking stdin check on Windows
            import msvcrt
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in [b'\r', b'\n', b' ']:
                    print("\n[Mediator] Input received! Resuming submission...")
                    return True
            
            # Also try reading stdin directly
            try:
                if sys.stdin.readable():
                    import threading
                    result = [None]
                    def read_stdin():
                        try:
                            result[0] = sys.stdin.readline()
                        except Exception:
                            pass
                    t = threading.Thread(target=read_stdin, daemon=True)
                    t.start()
                    t.join(timeout=0.5)
                    if result[0] is not None and len(result[0].strip()) >= 0 and result[0] != '':
                        print("\n[Mediator] Stdin input received! Resuming submission...")
                        return True
            except Exception:
                pass
            
            time.sleep(1.0)
    else:
        # Interactive console mode: use msvcrt
        import msvcrt
        while time.time() - start_time < timeout_sec:
            remaining = int(timeout_sec - (time.time() - start_time))
            sys.stdout.write(f"\r[Mediator Timer] {remaining}s remaining... (Press ENTER when done) ")
            sys.stdout.flush()
            
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key in [b'\r', b'\n', b' ']:
                    print("\n[Mediator] User intervention confirmed! Resuming submission...")
                    return True
            time.sleep(1.0)

    print("\n[Mediator] Timer expired (AFK). Gracefully saving state & skipping to next job.")
    return False

def dismiss_overlays(page):
    """Dismisses guest sign-in modals, cookie consent banners, or backdrop popups."""
    dismiss_selectors = [
        'button[aria-label="Dismiss"]',
        'button.modal__dismiss',
        'button[data-tracking-control-name*="modal_dismiss"]',
        'button[data-tracking-control-name*="sign-in-modal_dismiss"]',
        'button:has-text("Dismiss")',
        'button:has-text("Not now")',
        'button:has-text("Reject")',
        'button:has-text("Accept")'
    ]
    for sel in dismiss_selectors:
        try:
            btn = page.locator(sel)
            if btn.count() > 0 and btn.first.is_visible():
                btn.first.click()
                time.sleep(0.5)
        except Exception:
            pass

    # Press Escape to clear any remaining modal focus
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass

def apply_to_job(folder_path: str, mode: str = "assisted", max_deadline_sec: float = 90.0, mediator_timeout_sec: int = 45):
    # Guard: Brave must be closed so Playwright can use the Default profile
    import subprocess
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq brave.exe'], capture_output=True, text=True)
    if 'brave.exe' in result.stdout.lower():
        print("\n" + "=" * 65)
        print("!! BRAVE IS CURRENTLY RUNNING !!")
        print("Please close ALL Brave windows first, then re-run this command.")
        print("(Playwright needs exclusive access to your Default Brave profile.)")
        print("=" * 65)
        sys.exit(1)

    package_file = os.path.join(folder_path, "application_package.json")
    job_file = os.path.join(folder_path, "job_details.json")

    if not os.path.exists(package_file) or not os.path.exists(job_file):
        raise FileNotFoundError(f"Missing application package in {folder_path}")

    with open(package_file, "r", encoding="utf-8") as f:
        pkg = json.load(f)
    with open(job_file, "r", encoding="utf-8") as f:
        job = json.load(f)

    job_id = job["id"]
    company = job["company"]
    title = job["title"]
    job_url = job["job_url"]
    resume_path = os.path.abspath(pkg["resume_path"])

    print(f"\n" + "=" * 60)
    print(f"🚀 [APPLY ENGINE] Starting Application: {company} - {title}")
    print(f"🔗 URL: {job_url}")
    print(f"📄 Resume: {resume_path}")
    print(f"⚙️  Mode: {mode.upper()} (Max deadline: {max_deadline_sec}s)")
    print("=" * 60)

    overall_start = time.time()

    with sync_playwright() as p:
        # Launch Brave using the user's Default profile (already logged into LinkedIn)
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            executable_path=BRAVE_EXE,
            headless=False,
            viewport={"width": 1280, "height": 950},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--profile-directory=Default"
            ]
        )
        page = context.new_page()

        try:
            # 1. Navigate to Job URL
            print("[1/5] Navigating to job portal...")
            try:
                page.goto(job_url, wait_until="domcontentloaded", timeout=25000)
            except Exception as e:
                print(f"Navigation note: {e}. Proceeding with active DOM...")
            time.sleep(2.0)

            # Dismiss annoying popups/guest modals
            dismiss_overlays(page)

            # 2. Upload Resume PDF (Sub-second file handler)
            print("[2/5] Locating and attaching 2-page resume PDF...")
            file_inputs = page.locator('input[type="file"]')
            if file_inputs.count() > 0:
                try:
                    file_inputs.first.set_input_files(resume_path)
                    print(f"      ✅ Resume attached via input[type='file']: {os.path.basename(resume_path)}")
                    time.sleep(1.5)
                except Exception as e:
                    print(f"      ⚠️ File upload note: {e}")
            else:
                print("      ℹ️ No direct file input on first view (checking apply modal).")

            # 3. Autofill Standard Contact Information
            print("[3/5] Autofilling canonical candidate fields...")
            cand = pkg["candidate"]
            field_mappings = [
                (['#first_name', 'input[name*="first_name" i]', 'input[name*="firstName" i]', 'input[id*="first" i]'], cand["first_name"]),
                (['#last_name', 'input[name*="last_name" i]', 'input[name*="lastName" i]', 'input[id*="last" i]'], cand["last_name"]),
                (['#email', 'input[type="email"]', 'input[name*="email" i]', 'input[id*="email" i]'], cand["email"]),
                (['#phone', 'input[type="tel"]', 'input[name*="phone" i]', 'input[id*="phone" i]'], cand["phone"]),
                (['#candidate-location', 'input[name*="city" i]', 'input[name*="location" i]'], cand["city"]),
                (['input[name*="linkedin" i]', 'input[id*="linkedin" i]', 'input[placeholder*="linkedin" i]'], cand["links"]["linkedin"]),
                (['input[name*="website" i]', 'input[id*="website" i]', 'input[placeholder*="portfolio" i]'], cand["links"]["portfolio"]),
                (['input[name*="github" i]', 'input[id*="github" i]'], cand["links"]["github"]),
            ]

            for selectors, val in field_mappings:
                for sel in selectors:
                    try:
                        loc = page.locator(sel)
                        if loc.count() > 0 and loc.first.is_visible():
                            loc.first.fill(val)
                            time.sleep(0.1)
                            break
                    except Exception:
                        pass

            # 4. Check for Apply Buttons (Arabic & English)
            apply_btn_selectors = [
                'button:has-text("Easy Apply")',
                'button:has-text("Apply Now")',
                'button:has-text("Apply")',
                'button:has-text("التقدم")',
                'a:has-text("التقدم")',
                'a:has-text("Apply")'
            ]
            for btn_sel in apply_btn_selectors:
                apply_btn = page.locator(btn_sel)
                if apply_btn.count() > 0 and apply_btn.first.is_visible():
                    print(f"      👉 Found Apply button ('{btn_sel}'), clicking...")
                    try:
                        apply_btn.first.click()
                        time.sleep(2.0)
                        
                        # Re-check for file upload in the new modal
                        modal_file_inputs = page.locator('input[type="file"]')
                        if modal_file_inputs.count() > 0:
                            modal_file_inputs.first.set_input_files(resume_path)
                            print("      ✅ Resume attached in application modal.")
                        break
                    except Exception as e:
                        print(f"      Apply click note: {e}")

            # 5. Handle Next / Review / Submit flow
            print("[4/5] Checking submission readiness...")
            
            # If in DRY-RUN mode
            if mode == "dry-run":
                preview_shot = os.path.join(folder_path, "dry_run_preview.png")
                page.screenshot(path=preview_shot, full_page=True)
                print(f"      📸 Dry-run complete. Screenshot saved: {preview_shot}")
                print("      🛑 [DRY-RUN] Skipping final submit click.")
                context.close()
                return "dry-run-success"

            submit_btn = page.locator('button[type="submit"], button:has-text("Submit application"), button:has-text("Submit"), button:has-text("Review"), button:has-text("إرسال")')
            
            needs_mediation = False
            if submit_btn.count() == 0 or not submit_btn.first.is_visible() or submit_btn.first.is_disabled():
                needs_mediation = True

            if mode == "assisted" or needs_mediation:
                intervened = prompt_mediator(company, title, timeout_sec=mediator_timeout_sec)
                if not intervened:
                    diag_shot = os.path.join(folder_path, "timeout_diagnostic.png")
                    page.screenshot(path=diag_shot, full_page=True)
                    
                    conn = get_db_connection()
                    conn.execute("UPDATE jobs SET status = 'needs_manual_review', notes = 'Skipped by mediator timeout (AFK)' WHERE id = ?", (job_id,))
                    conn.commit()
                    conn.close()
                    
                    print(f"      💾 State saved as 'needs_manual_review'. Screenshot: {diag_shot}")
                    context.close()
                    return "skipped-afk"

            # 6. Execute Final Submission & Capture Receipt
            print("[5/5] Submitting application and recording proof...")
            receipt_path = os.path.join(folder_path, "receipt.png")
            
            submit_btn = page.locator('button[type="submit"], button:has-text("Submit application"), button:has-text("Submit"), button:has-text("إرسال")')
            if submit_btn.count() > 0 and submit_btn.first.is_visible():
                submit_btn.first.click()
                time.sleep(3.5)

            # Capture full-page proof
            page.screenshot(path=receipt_path, full_page=True)
            print(f"      📸 Submission receipt saved: {receipt_path}")

            # Update DB to 'applied'
            conn = get_db_connection()
            cur = conn.cursor()
            now_iso = datetime.datetime.now().isoformat()
            cur.execute("""
                UPDATE jobs 
                SET status = 'applied', 
                    applied_at = ?, 
                    applied_receipt = ? 
                WHERE id = ?
            """, (now_iso, receipt_path, job_id))
            conn.commit()
            conn.close()

            print(f"🎉 [SUCCESS] Applied to {company} ({title})! Status updated to 'applied'.")
            context.close()
            return "applied"

        except Exception as e:
            err_shot = os.path.join(folder_path, "error_diagnostic.png")
            try:
                page.screenshot(path=err_shot, full_page=True)
            except Exception:
                pass
            print(f"\n❌ Error during application to {company}: {e}")
            
            conn = get_db_connection()
            conn.execute("UPDATE jobs SET status = 'needs_manual_review', notes = ? WHERE id = ?", (f"Error: {str(e)[:200]}", job_id))
            conn.commit()
            conn.close()
            
            context.close()
            return "error"

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Career-Ops Fail-Safe Browser Apply Engine")
    parser.add_argument("--folder", type=str, help="Application folder path to apply to")
    parser.add_argument("--job-id", type=str, help="Job ID in jobs.db")
    parser.add_argument("--mode", type=str, choices=["assisted", "dry-run", "auto"], default="assisted", help="Execution mode")
    parser.add_argument("--timeout", type=int, default=45, help="Mediator countdown timeout in seconds")
    args = parser.parse_args()

    target_folder = args.folder
    if not target_folder and args.job_id:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT application_folder FROM jobs WHERE id = ?", (args.job_id,))
        row = cur.fetchone()
        conn.close()
        if row and row[0]:
            target_folder = row[0]
        else:
            print(f"Job ID {args.job_id} does not have an application_folder yet. Run fast_ats_tailor.py first.")
            sys.exit(1)

    if not target_folder:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT application_folder FROM jobs WHERE status = 'tailored' AND application_folder IS NOT NULL LIMIT 1")
        row = cur.fetchone()
        conn.close()
        if row and row[0]:
            target_folder = row[0]
        else:
            print("No tailored jobs found awaiting application.")
            sys.exit(0)

    apply_to_job(target_folder, mode=args.mode, mediator_timeout_sec=args.timeout)

if __name__ == "__main__":
    main()
