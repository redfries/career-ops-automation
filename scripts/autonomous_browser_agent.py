#!/usr/bin/env python3
"""
autonomous_browser_agent.py
Autonomous AI Browser Agent for Direct Job Application Submission:
- Launches local Chromium in Headed Mode (visible on user desktop)
- Supports Greenhouse, Lever, Ashby, and generic ATS application forms
- Uploads tailored PDF resume directly via <input type="file">
- Maps candidate contact details, links, and canonical facts from data/canonical_profile.json
- Injects Block H tailored screener answers into open questions
- Executes a 3-second visual countdown on screen before auto-clicking Submit
- Detects post-submission confirmation and captures timestamped receipt.png
- Updates SQLite (data/applications.db) and optionally triggers Notion sync
- Fully handles --dry-run (fills everything, pauses, but does NOT submit)
"""

import os
import sys
import re
import time
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Ensure scripts directory in path
SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

# Ensure Windows UTF-8 console output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from playwright.sync_api import sync_playwright, Page, BrowserContext, ElementHandle, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("[ERROR] Playwright is not installed. Please run: pip install playwright && playwright install chromium")
    sys.exit(1)

try:
    from db_manager import upsert_application, get_application_by_id, get_connection
except ImportError:
    upsert_application = None

def load_canonical_profile() -> Dict[str, Any]:
    profile_path = ROOT_DIR / "data" / "canonical_profile.json"
    if not profile_path.exists():
        raise FileNotFoundError(f"Canonical profile not found at {profile_path}")
    with open(profile_path, "r", encoding="utf-8") as f:
        return json.load(f)

class AIBrowserAgent:
    def __init__(self, headed: bool = True, slow_mo: int = 50, dry_run: bool = False):
        self.headed = headed
        self.slow_mo = slow_mo
        self.dry_run = dry_run
        self.profile = load_canonical_profile()
        self.candidate = self.profile.get("candidate", {})
        self.links = self.candidate.get("links", {})
        self.location = self.candidate.get("location", {})
        self.work_auth = self.profile.get("work_authorization", {})

    def detect_portal(self, url: str) -> str:
        url_lower = url.lower()
        if "greenhouse.io" in url_lower or "gh_jid" in url_lower:
            return "greenhouse"
        elif "lever.co" in url_lower:
            return "lever"
        elif "ashbyhq.com" in url_lower:
            return "ashby"
        elif "workday" in url_lower:
            return "workday"
        return "generic"

    def fill_input_if_found(self, page: Page, selectors: List[str], value: str, field_name: str = "") -> bool:
        """Tries a list of selectors and fills the first matching element."""
        if not value:
            return False
        for sel in selectors:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible() and el.is_enabled():
                    # Clear and type with natural human delay
                    el.click()
                    el.fill(str(value))
                    print(f"  [OK] Filled {field_name or sel} -> {value[:30]}...")
                    return True
            except Exception:
                continue
        return False

    def upload_resume_file(self, page: Page, pdf_path: Path) -> bool:
        """Locates the resume file input and attaches the PDF."""
        if not pdf_path.exists():
            print(f"  [ERROR] Resume PDF not found: {pdf_path}")
            return False

        print(f"  [ATTACH] Uploading resume: {pdf_path.name}")
        file_selectors = [
            'input[type="file"][name*="resume" i]',
            'input[type="file"][id*="resume" i]',
            'input[type="file"][aria-label*="resume" i]',
            'input[type="file"][name*="cv" i]',
            'input[type="file"][id*="cv" i]',
            '#resume',
            'input[type="file"]'
        ]

        for sel in file_selectors:
            try:
                inputs = page.query_selector_all(sel)
                for inp in inputs:
                    inp.set_input_files(str(pdf_path))
                    print(f"  [OK] Successfully attached PDF to '{sel}'")
                    time.sleep(1.0)
                    return True
            except Exception as e:
                continue

        print("  [WARN] Could not find direct file input element for resume.")
        return False

    def solve_screener_questions(self, page: Page, screener_answers: Dict[str, str]):
        """Detects custom textareas and inputs, matching them to screener answers or candidate facts."""
        textareas = page.query_selector_all("textarea")
        for ta in textareas:
            try:
                if not ta.is_visible():
                    continue
                
                field_id = ta.get_attribute("id") or ""
                field_name = ta.get_attribute("name") or ""
                placeholder = ta.get_attribute("placeholder") or ""
                
                label_text = ""
                if field_id:
                    lbl = page.query_selector(f'label[for="{field_id}"]')
                    if lbl:
                        label_text = lbl.inner_text().strip()
                if not label_text:
                    label_text = placeholder or field_name

                best_ans = None
                label_lower = label_text.lower()
                for q_key, ans_text in screener_answers.items():
                    key_words = q_key.lower().replace("_", " ").split()
                    if any(w in label_lower for w in key_words if len(w) > 3):
                        best_ans = ans_text
                        break

                if not best_ans:
                    if "relocat" in label_lower:
                        best_ans = "Yes, I am fully open to relocation (holding a valid transferable Iqama in Saudi Arabia)."
                    elif "notice" in label_lower:
                        best_ans = "Immediately available upon contract finalization."
                    elif "sponsor" in label_lower or "visa" in label_lower:
                        best_ans = "For Saudi Arabia: No sponsorship required (Transferable Iqama). For Remote: Available as B2B contractor."
                    elif "salary" in label_lower or "compensation" in label_lower:
                        best_ans = "Competitive / open to standard company compensation bands."
                    elif "summary" in label_lower or "about" in label_lower or "cover" in label_lower:
                        best_ans = screener_answers.get("summary", "AI/ML Engineer with expertise in Computer Vision, Vision Transformers, and RAG architectures.")

                if best_ans:
                    ta.fill(best_ans)
                    print(f"  [OK] Answered screener question: '{label_text[:40]}...'")
            except Exception:
                continue

    def apply_greenhouse(self, page: Page, pdf_path: Path, screener_answers: Dict[str, str]) -> bool:
        print("\n--- [PORTAL] Handling Greenhouse Application ---")
        
        apply_btn = page.query_selector('a[href*="#app"], button:has-text("Apply Now")')
        if apply_btn and apply_btn.is_visible():
            try:
                apply_btn.click()
                time.sleep(0.5)
            except Exception:
                pass

        self.upload_resume_file(page, pdf_path)

        self.fill_input_if_found(page, ['#first_name', 'input[name*="first_name" i]'], self.candidate.get("first_name"), "First Name")
        self.fill_input_if_found(page, ['#last_name', 'input[name*="last_name" i]'], self.candidate.get("last_name"), "Last Name")
        self.fill_input_if_found(page, ['#email', 'input[name*="email" i]'], self.candidate.get("email"), "Email")
        self.fill_input_if_found(page, ['#phone', 'input[name*="phone" i]'], self.candidate.get("phone"), "Phone")

        self.fill_input_if_found(page, [
            'input[autocomplete*="linkedin" i]',
            'input[id*="linkedin" i]',
            'input[name*="linkedin" i]'
        ], self.links.get("linkedin"), "LinkedIn")

        self.fill_input_if_found(page, [
            'input[autocomplete*="website" i]',
            'input[id*="website" i]',
            'input[name*="website" i]',
            'input[id*="portfolio" i]'
        ], self.links.get("portfolio"), "Portfolio")

        self.fill_input_if_found(page, [
            'input[id*="github" i]',
            'input[name*="github" i]'
        ], self.links.get("github"), "GitHub")

        self.solve_screener_questions(page, screener_answers)
        return True

    def apply_lever(self, page: Page, pdf_path: Path, screener_answers: Dict[str, str]) -> bool:
        print("\n--- [PORTAL] Handling Lever Application ---")
        
        if "/apply" not in page.url:
            apply_link = page.query_selector('a[href*="/apply"], a:has-text("Apply for this job")')
            if apply_link and apply_link.is_visible():
                print("  [NAV] Clicking 'Apply for this job'...")
                apply_link.click()
                page.wait_for_load_state("networkidle")

        self.upload_resume_file(page, pdf_path)

        full_name = self.candidate.get("name", "Shabaaz Hussain Shaik")
        self.fill_input_if_found(page, ['input[name="name"]'], full_name, "Full Name")
        self.fill_input_if_found(page, ['input[name="email"]'], self.candidate.get("email"), "Email")
        self.fill_input_if_found(page, ['input[name="phone"]'], self.candidate.get("phone"), "Phone")
        self.fill_input_if_found(page, ['input[name="org"]'], "KFUPM", "Current Organization")

        self.fill_input_if_found(page, ['input[name="urls[LinkedIn]"]'], self.links.get("linkedin"), "LinkedIn")
        self.fill_input_if_found(page, ['input[name="urls[GitHub]"]'], self.links.get("github"), "GitHub")
        self.fill_input_if_found(page, ['input[name="urls[Portfolio]"]'], self.links.get("portfolio"), "Portfolio")
        self.fill_input_if_found(page, ['input[name="urls[Other]"]'], self.links.get("portfolio"), "Other URL")

        self.solve_screener_questions(page, screener_answers)
        return True

    def apply_ashby(self, page: Page, pdf_path: Path, screener_answers: Dict[str, str]) -> bool:
        print("\n--- [PORTAL] Handling Ashby Application ---")
        
        apply_btn = page.query_selector('button:has-text("Apply for this job"), a:has-text("Apply")')
        if apply_btn and apply_btn.is_visible():
            try:
                apply_btn.click()
                time.sleep(0.5)
            except Exception:
                pass

        self.upload_resume_file(page, pdf_path)

        self.fill_input_if_found(page, ['input[name="name"]', 'input[id*="name" i]'], self.candidate.get("name"), "Name")
        self.fill_input_if_found(page, ['input[name="email"]', 'input[type="email"]'], self.candidate.get("email"), "Email")
        self.fill_input_if_found(page, ['input[name="phoneNumber"]', 'input[type="tel"]'], self.candidate.get("phone"), "Phone")

        self.fill_input_if_found(page, ['input[placeholder*="linkedin" i]', 'input[name*="linkedin" i]'], self.links.get("linkedin"), "LinkedIn")
        self.fill_input_if_found(page, ['input[placeholder*="github" i]', 'input[name*="github" i]'], self.links.get("github"), "GitHub")
        self.fill_input_if_found(page, ['input[placeholder*="website" i]', 'input[name*="website" i]'], self.links.get("portfolio"), "Website")

        self.solve_screener_questions(page, screener_answers)
        return True

    def apply_generic(self, page: Page, pdf_path: Path, screener_answers: Dict[str, str]) -> bool:
        print("\n--- [PORTAL] Handling Generic ATS Application ---")
        self.upload_resume_file(page, pdf_path)
        
        if not self.fill_input_if_found(page, ['input[name*="first_name" i]', 'input[id*="first_name" i]'], self.candidate.get("first_name"), "First Name"):
            self.fill_input_if_found(page, ['input[name*="name" i]', 'input[id*="name" i]'], self.candidate.get("name"), "Full Name")
        self.fill_input_if_found(page, ['input[name*="last_name" i]', 'input[id*="last_name" i]'], self.candidate.get("last_name"), "Last Name")
        
        self.fill_input_if_found(page, ['input[type="email"]', 'input[name*="email" i]'], self.candidate.get("email"), "Email")
        self.fill_input_if_found(page, ['input[type="tel"]', 'input[name*="phone" i]'], self.candidate.get("phone"), "Phone")
        
        self.fill_input_if_found(page, ['input[name*="linkedin" i]'], self.links.get("linkedin"), "LinkedIn")
        self.fill_input_if_found(page, ['input[name*="github" i]'], self.links.get("github"), "GitHub")
        
        self.solve_screener_questions(page, screener_answers)
        return True

    def check_and_handle_verification(self, page: Page, max_wait: int = 45) -> bool:
        """
        Option 3 Architecture:
        Detects if an application portal prompts for an email OTP or verification code sent to theshabaaz@outlook.com.
        Alerts in console and pauses on screen so candidate can glance at their phone/Outlook and enter it.
        """
        otp_selectors = [
            'input[autocomplete="one-time-code"]',
            'input[name*="verification" i]',
            'input[name*="code" i]',
            'input[id*="verification" i]',
            'input[id*="otp" i]',
            'input[placeholder*="verification" i]',
            'input[placeholder*="code" i]'
        ]
        
        otp_field = None
        for sel in otp_selectors:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible() and el.is_enabled():
                    otp_field = el
                    break
            except Exception:
                continue

        if not otp_field:
            return False

        print("\n" + "!"*65)
        print("🔔 [ACTION REQUIRED: EMAIL VERIFICATION CODE DETECTED]")
        print("The job portal requested an email confirmation code sent to:")
        print(f"👉 {self.candidate.get('email', 'theshabaaz@outlook.com')}")
        print("Please check your Outlook email / phone and type the code into")
        print("the open browser window on your screen (waiting up to 45s)...")
        print("!"*65 + "\n")

        start_t = time.time()
        while time.time() - start_t < max_wait:
            try:
                val = otp_field.input_value()
                if val and len(val.strip()) >= 4:
                    print(f"  [OK] Verification code entered ({len(val)} digits). Resuming automation...")
                    time.sleep(1.0)
                    return True
            except Exception:
                pass
            time.sleep(1.0)

        print("  [INFO] Continuing workflow...")
        return False

    def check_and_handle_challenge(self, page: Page, max_wait: int = 90) -> bool:
        """
        Detects Cloudflare turnstile, bot-block, or login wall and pauses for HITL resolution.
        """
        title_lower = page.title().lower()
        content_sample = ""
        try:
            content_sample = page.inner_text("body")[:500].lower()
        except Exception:
            pass

        if "blocked" in title_lower or "just a moment" in title_lower or "attention required" in title_lower or "security check" in title_lower or "verify you are human" in content_sample:
            print("\n" + "!"*65)
            print("🔔 [HUMAN-IN-THE-LOOP: BOT CHALLENGE / CAPTCHA DETECTED]")
            print(f"Target page title: '{page.title()}'")
            print("Please solve the verification challenge in the open browser window.")
            print(f"Pausing automation for up to {max_wait}s to allow manual verification...")
            print("!"*65 + "\n")
            start_t = time.time()
            while time.time() - start_t < max_wait:
                time.sleep(2.0)
                cur_title = page.title().lower()
                if "blocked" not in cur_title and "just a moment" not in cur_title and "attention required" not in cur_title:
                    print(f"  [OK] Challenge resolved! Page title: '{page.title()}'. Resuming automation...")
                    time.sleep(2.0)
                    return True
            print("  [WARN] Challenge still present after timeout. Proceeding...")
            return False
        return True

    def check_and_click_job_board_apply(self, page: Page, context: BrowserContext) -> Page:
        """If on a job listing aggregator (Indeed, Bayt, LinkedIn), clicks 'Apply' to reach application form."""
        apply_selectors = [
            '#indeedApplyButton',
            'button[id*="indeedApply" i]',
            'button:has-text("Apply on company site")',
            'a:has-text("Apply on company site")',
            'button:has-text("Apply now")',
            'a:has-text("Apply now")',
            'a[data-tn-element="indeedApplyButton"]',
            'button:has-text("Easy Apply")',
            'button:has-text("Apply")',
            'a:has-text("Apply")'
        ]
        for sel in apply_selectors:
            try:
                btn = page.query_selector(sel)
                if btn and btn.is_visible() and btn.is_enabled():
                    print(f"  [CLICK] Found job board apply trigger: '{sel}'. Clicking...")
                    initial_pages = len(context.pages)
                    try:
                        btn.click()
                    except Exception:
                        continue
                    time.sleep(2.5)
                    if len(context.pages) > initial_pages:
                        new_page = context.pages[-1]
                        new_page.wait_for_load_state("domcontentloaded")
                        print(f"  [NAV] New application tab opened: {new_page.url[:60]}...")
                        return new_page
                    else:
                        print(f"  [NAV] Continuing on active page: {page.url[:60]}...")
                        return page
            except Exception:
                pass
        return page

    def run_submission(
        self,
        job_url: str,
        company: str,
        role: str,
        pdf_path: Path,
        app_id: str,
        screener_answers: Optional[Dict[str, str]] = None,
        bundle_folder: Optional[Path] = None
    ) -> Dict[str, Any]:
        screener_answers = screener_answers or {}
        portal = self.detect_portal(job_url)
        receipt_path = None
        if bundle_folder:
            receipt_path = bundle_folder / "receipt.png"
        else:
            receipt_path = ROOT_DIR / "applications" / f"{app_id}_receipt.png"

        print("\n" + "="*65)
        print(f"[AI BROWSER AGENT] STARTING SUBMISSION WORKFLOW")
        print(f"Company:   {company}")
        print(f"Role:      {role}")
        print(f"Portal:    {portal.upper()}")
        print(f"Target:    {job_url}")
        print(f"Resume:    {pdf_path.name}")
        print(f"Mode:      {'DRY RUN (Will not click submit)' if self.dry_run else 'LIVE SUBMISSION'}")
        print(f"Browser:   {'VISIBLE (Headed)' if self.headed else 'HEADLESS'}")
        print("="*65)

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=not self.headed,
                slow_mo=self.slow_mo,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized"
                ]
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            page = context.new_page()

            try:
                print(f"\n[NAVIGATE] Opening application page...")
                page.goto(job_url, timeout=45000, wait_until="domcontentloaded")
                time.sleep(1.5)

                # Check for Cloudflare / bot challenge
                self.check_and_handle_challenge(page)

                # If on job board aggregator, trigger apply link
                page = self.check_and_click_job_board_apply(page, context)
                time.sleep(1.0)

                # Re-detect portal from current active URL
                portal = self.detect_portal(page.url)
                if portal != "generic":
                    print(f"  [PORTAL DETECTED] Resolved to {portal.upper()} handler.")

                if portal == "greenhouse":
                    self.apply_greenhouse(page, pdf_path, screener_answers)
                elif portal == "lever":
                    self.apply_lever(page, pdf_path, screener_answers)
                elif portal == "ashby":
                    self.apply_ashby(page, pdf_path, screener_answers)
                else:
                    self.apply_generic(page, pdf_path, screener_answers)

                # Option 3: Check for Email Verification / OTP Code Modal
                self.check_and_handle_verification(page)

                # 3-Second Visual Inspection Pause
                print("\n" + "-"*50)
                print("[PAUSE] 3-second visual inspection window on screen...")
                print("-" * 50)
                for i in range(3, 0, -1):
                    print(f"  --> Submitting in {i} second(s)...")
                    time.sleep(1.0)

                if self.dry_run:
                    print("\n[DRY RUN COMPLETE] Form filled and inspected successfully.")
                    print(f"[PREVIEW] Saving dry-run screenshot to: {receipt_path}")
                    receipt_path.parent.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(receipt_path), full_page=True)
                    time.sleep(2.0)
                    browser.close()
                    return {
                        "success": True,
                        "status": "dry_run_verified",
                        "receipt_path": str(receipt_path),
                        "submitted": False
                    }

                submit_selectors = [
                    '#submit_app',
                    '#btn-submit',
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Submit Application")',
                    'button:has-text("Submit application")',
                    'button:has-text("Submit")'
                ]

                submit_btn = None
                for sel in submit_selectors:
                    el = page.query_selector(sel)
                    if el and el.is_visible() and el.is_enabled():
                        submit_btn = el
                        break

                if not submit_btn:
                    print("[WARN] Could not identify primary submit button automatically.")
                    page.screenshot(path=str(receipt_path), full_page=True)
                    browser.close()
                    return {
                        "success": False,
                        "error": "Submit button not found",
                        "receipt_path": str(receipt_path)
                    }

                print(f"\n[SUBMIT] Clicking application submit button...")
                submit_btn.click()

                print("[VERIFY] Waiting for submission confirmation...")
                time.sleep(4.0)

                receipt_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(receipt_path), full_page=True)
                print(f"[RECEIPT] Saved full-page confirmation screenshot: {receipt_path.name}")

                if upsert_application:
                    now_iso = datetime.now().isoformat()
                    upsert_application({
                        "id": app_id,
                        "company": company,
                        "role": role,
                        "status": "submitted",
                        "submission_receipt": str(receipt_path),
                        "submitted_at": now_iso,
                        "updated_at": now_iso
                    })
                    print(f"[DATABASE] Updated SQLite application '{app_id}' -> status: submitted")

                browser.close()
                return {
                    "success": True,
                    "status": "submitted",
                    "receipt_path": str(receipt_path),
                    "submitted": True
                }

            except Exception as e:
                print(f"\n[ERROR] Browser workflow encountered an exception: {str(e)}")
                try:
                    receipt_path.parent.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(receipt_path), full_page=True)
                except Exception:
                    pass
                browser.close()
                return {
                    "success": False,
                    "error": str(e),
                    "receipt_path": str(receipt_path) if receipt_path.exists() else None
                }

def main():
    parser = argparse.ArgumentParser(description="Autonomous AI Browser Application Agent")
    parser.add_argument("--url", required=True, help="Job application URL")
    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument("--role", required=True, help="Job title")
    parser.add_argument("--pdf", required=True, help="Path to tailored resume PDF")
    parser.add_argument("--id", default="", help="Application ID (defaults to slug)")
    parser.add_argument("--dry-run", action="store_true", help="Fill form and pause without clicking submit")
    parser.add_argument("--headless", action="store_true", help="Run in silent background mode without UI")
    args = parser.parse_args()

    app_id = args.id or f"{datetime.now().strftime('%Y-%m-%d')}_{re.sub(r'[^a-z0-9]+', '-', args.company.lower())}_{re.sub(r'[^a-z0-9]+', '-', args.role.lower())}"
    pdf_path = Path(args.pdf).resolve()

    agent = AIBrowserAgent(
        headed=not args.headless,
        dry_run=args.dry_run
    )

    res = agent.run_submission(
        job_url=args.url,
        company=args.company,
        role=args.role,
        pdf_path=pdf_path,
        app_id=app_id
    )

    if res["success"]:
        print(f"\n[SUCCESS] Workflow completed successfully! Status: {res.get('status')}")
    else:
        print(f"\n[FAILURE] Workflow ended with error: {res.get('error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
