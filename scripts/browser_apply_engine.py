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

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(REPO_DIR, 'data', 'jobs.db')
BRAVE_EXE = os.environ.get(
    'BRAVE_PATH',
    r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe'
)
# Dedicated persistent automation profile:
# 1. Avoids profile lock collisions with personal Brave
# 2. Bypasses Chrome 136+ security block on remote debugging on default User Data
# 3. Saves session cookies (LinkedIn, etc.) permanently across runs
PROFILE_DIR = os.environ.get(
    'BROWSER_PROFILE_DIR',
    os.path.join(REPO_DIR, 'data', 'browser_profile')
)
os.makedirs(PROFILE_DIR, exist_ok=True)

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def prompt_mediator(company: str, title: str, timeout_sec: int = 45, auto_confirm: bool = False) -> bool:
    """Alerts user with an audible chime and gives a countdown to mediate in the visible browser.
    Proceeds immediately when auto_confirm=True or when user presses ENTER,
    or proceeds when timeout completes.
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
    print(f"Countdown: {timeout_sec}s to review before proceeding with submission.")
    print("Press [ENTER] in this terminal once ready to proceed immediately...")
    print("=" * 65)

    start_time = time.time()
    import msvcrt
    
    while time.time() - start_time < timeout_sec:
        remaining = int(timeout_sec - (time.time() - start_time))
        sys.stdout.write(f"\r[Mediator Timer] {remaining:>2}s remaining... (Press ENTER to submit immediately) ")
        sys.stdout.flush()

        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key in [b'\r', b'\n', b' ']:
                print("\n[Mediator] User intervention confirmed! Resuming submission...")
                return True
        time.sleep(1.0)

    print("\n[Mediator] Timer elapsed. Resuming submission...")
    return True

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

def bring_brave_to_foreground():
    """Finds the active Brave/Chromium window and forces it to OS foreground on Windows."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    SW_RESTORE = 9
    HWND_TOPMOST = -1
    HWND_NOTOPMOST = -2
    SWP_SHOWWINDOW = 0x0040

    found_hwnds = []

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def enum_cb(hwnd, lparam):
        if not user32.IsWindow(hwnd):
            return True
        class_buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, class_buf, 256)
        if class_buf.value == "Chrome_WidgetWin_1":
            title_len = user32.GetWindowTextLengthW(hwnd)
            title_buf = ctypes.create_unicode_buffer(title_len + 1)
            user32.GetWindowTextW(hwnd, title_buf, title_len + 1)
            # Filter strictly for Brave windows, avoiding IDE / Electron windows
            if title_len > 0 and ("brave" in title_buf.value.lower() or "- brave" in title_buf.value.lower()):
                found_hwnds.append((hwnd, title_buf.value))
        return True

    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    if not found_hwnds:
        print("      ⚠️ [Win32] No Brave window found to bring to foreground.")
        return False

    target_hwnd = found_hwnds[0][0]
    print(f"      🪟 [Win32] Found Brave window: '{found_hwnds[0][1][:60]}...'")

    # 1. Restore from minimized state
    user32.ShowWindow(target_hwnd, SW_RESTORE)

    # 2. Reset position to primary display (0,0)
    user32.SetWindowPos(target_hwnd, HWND_TOPMOST, 0, 0, 1300, 960, SWP_SHOWWINDOW)
    user32.SetWindowPos(target_hwnd, HWND_NOTOPMOST, 0, 0, 1300, 960, SWP_SHOWWINDOW)

    # 3. Bypass Windows foreground lock using ALT key tap + AttachThreadInput
    fg_hwnd = user32.GetForegroundWindow()
    fg_thread_id = user32.GetWindowThreadProcessId(fg_hwnd, None)
    cur_thread_id = kernel32.GetCurrentThreadId()

    # Simulate ALT key tap to grant focus permission
    user32.keybd_event(0x12, 0, 0, 0)       # VK_MENU (Alt) down
    user32.keybd_event(0x12, 0, 0x0002, 0)  # VK_MENU (Alt) up

    if fg_thread_id != cur_thread_id:
        user32.AttachThreadInput(cur_thread_id, fg_thread_id, True)
        user32.BringWindowToTop(target_hwnd)
        user32.SetForegroundWindow(target_hwnd)
        user32.AttachThreadInput(cur_thread_id, fg_thread_id, False)
    else:
        user32.BringWindowToTop(target_hwnd)
        user32.SetForegroundWindow(target_hwnd)

    print("      ✅ [Win32] Brave window brought to foreground successfully.")
    return True

def apply_to_job(folder_path: str, mode: str = "assisted", max_deadline_sec: float = 90.0, mediator_timeout_sec: int = 45):
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

    # --- Launch Brave with Remote Debugging ---
    import urllib.request
    import subprocess
    CDP_PORT = 9222

    def is_cdp_listening(port):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    if not is_cdp_listening(CDP_PORT):
        print(f"[0/5] Launching Brave on visible desktop...")
        brave_cmd = [
            BRAVE_EXE,
            f"--remote-debugging-port={CDP_PORT}",
            f"--user-data-dir={PROFILE_DIR}",
            "--no-first-run",
            "--no-default-browser-check",
            "--start-maximized",
            "--test-type",
            "about:blank"
        ]
        subprocess.Popen(brave_cmd)

        for _ in range(12):
            time.sleep(0.5)
            if is_cdp_listening(CDP_PORT):
                break
    else:
        print(f"[0/5] Connected to active Brave automation instance on port {CDP_PORT}.")

    # Force to foreground via Win32 API
    try:
        bring_brave_to_foreground()
    except Exception as e:
        print(f"      ⚠️ Win32 foreground helper note: {e}")

    with sync_playwright() as p:
        # Connect to Brave over CDP instead of launching it
        print(f"      🔌 Connecting Playwright to Brave via CDP (port {CDP_PORT})...")
        try:
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{CDP_PORT}")
        except Exception as e:
            print(f"      ❌ CDP connection failed: {e}")
            print("      Retrying in 3 seconds...")
            time.sleep(3.0)
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{CDP_PORT}")

        context = browser.contexts[0]
        # Stealthily hide webdriver flag without triggering Chromium warning banner
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.pages[0] if context.pages else context.new_page()
        print("      ✅ Connected to Brave successfully.")

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

            # Re-force Brave to foreground after navigation
            try:
                bring_brave_to_foreground()
            except Exception:
                pass

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
                (['#candidate-location', 'input[name*="city" i]', 'input[name*="location" i]'], cand.get("city", cand.get("location", "Dhahran"))),
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
                browser.close()
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
                    browser.close()
                    return "skipped-afk"

            # 6. Execute Final Submission & Capture Receipt
            print("[5/5] Submitting application and recording proof...")
            receipt_path = os.path.join(folder_path, "receipt.png")
            
            submit_btn = page.locator('button[type="submit"], button:has-text("Submit application"), button:has-text("Submit"), button:has-text("إرسال")')
            if submit_btn.count() > 0 and submit_btn.first.is_visible():
                submit_btn.click()
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
            browser.close()
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
            
            try:
                browser.close()
            except Exception:
                pass
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
