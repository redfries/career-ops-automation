#!/usr/bin/env python3
"""
start_engine.py
================================================================================
Career-Ops HITL Automation Engine - Master Cockpit & Command Orchestrator
================================================================================
A unified, standalone controller for:
- Sourcing AI/ML roles across Saudi Arabia, UAE, and Global Remote markets
- Scoring jobs against canonical evidence boundaries (Zero-Hallucination)
- Rendering Human-in-the-Loop decision cards
- Autonomous Playwright browser submission (headed mode with OTP pause)
- Resilient Notion synchronization and SQLite tracking
- Full system health diagnostics
================================================================================
"""

import os
import sys
import json
import time
import shutil
import sqlite3
import argparse
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure project root and scripts/ directory in sys.path
ROOT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Ensure Windows UTF-8 console output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Import core pipeline modules
from db_manager import get_connection, is_url_visited, mark_url_visited
from fast_ats_tailor import load_canonical_profile
from run_batch import evaluate_batch, print_chat_digest, apply_selected_jobs
from deep_reach import generate_outreach_dossier, print_dossier
from sync_to_notion import sync_applications_to_notion, load_env, get_database_schema

# ANSI color codes for rich terminal UI
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

def print_banner():
    banner = f"""{CYAN}{BOLD}
================================================================================
   ____                               ___             
  / ___|__ _ _ __ ___  ___ _ __      / _ \\ _ __  ___  
 | |   / _` | '__/ _ \\/ _ \\ '__|____| | | | '_ \\/ __| 
 | |__| (_| | | |  __/  __/ | |_____| |_| | |_) \\__ \\ 
  \\____\\__,_|_|  \\___|\\___|_|        \\___/| .__/|___/ 
                                          |_|         
   AUTONOMOUS HUMAN-IN-THE-LOOP JOB APPLICATION ENGINE
================================================================================{RESET}
 {DIM}Candidate: Shabaaz Hussain Shaik (AI / Machine Learning Engineer)
 Markets:   Saudi Arabia (Transferable Iqama), UAE, Global Remote
 System:    Playwright Headed Submitter + Fast ATS Tailor + Notion Kanban{RESET}
"""
    print(banner)

def run_diagnostics() -> bool:
    """Performs an exhaustive health check of all engine subsystems."""
    print(f"\n{BOLD}[SYSTEM HEALTH & READINESS DIAGNOSTICS]{RESET}\n")
    all_healthy = True

    # 1. Python Environment
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f" • Python Runtime:       {GREEN}v{py_ver}{RESET} ({sys.executable})")

    # 2. Canonical Profile
    prof_path = ROOT_DIR / "data" / "canonical_profile.json"
    if prof_path.exists():
        try:
            with open(prof_path, "r", encoding="utf-8") as f:
                prof = json.load(f)
            cand_name = prof.get("candidate", {}).get("name", "Unknown")
            print(f" • Canonical Profile:    {GREEN}OK{RESET} ({cand_name}, {prof_path.name})")
        except Exception as e:
            print(f" • Canonical Profile:    {RED}ERROR ({e}){RESET}")
            all_healthy = False
    else:
        print(f" • Canonical Profile:    {RED}MISSING ({prof_path}){RESET}")
        all_healthy = False

    # 3. SQLite Database
    db_path = ROOT_DIR / "data" / "applications.db"
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM applications")
            app_count = cur.fetchone()[0]
            conn.close()
            print(f" • SQLite Store:         {GREEN}OK{RESET} ({app_count} tracked applications)")
        except Exception as e:
            print(f" • SQLite Store:         {RED}ERROR ({e}){RESET}")
            all_healthy = False
    else:
        print(f" • SQLite Store:         {YELLOW}NOT INITIALIZED{RESET}")

    # 4. Playwright & Chromium
    try:
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start()
        browser = p.chromium.launch(headless=True)
        browser.close()
        p.stop()
        print(f" • Playwright Chromium:  {GREEN}OPERATIONAL{RESET} (Ready for visible headed submission)")
    except Exception as e:
        print(f" • Playwright Chromium:  {RED}FAILED ({e}){RESET}")
        print(f"   {YELLOW}Fix: pip install playwright && playwright install chromium{RESET}")
        all_healthy = False

    # 5. Tectonic XeTeX Compiler
    tectonic_bin = shutil.which("tectonic")
    if tectonic_bin:
        try:
            res = subprocess.run(["tectonic", "--version"], capture_output=True, text=True)
            ver = res.stdout.strip().split("\n")[0]
            print(f" • Tectonic Compiler:    {GREEN}OK{RESET} ({ver})")
        except Exception:
            print(f" • Tectonic Compiler:    {YELLOW}FOUND ON PATH{RESET} ({tectonic_bin})")
    else:
        print(f" • Tectonic Compiler:    {YELLOW}NOT FOUND ON PATH (Fast ATS HTML compiler available){RESET}")

    # 6. PyMuPDF (PDF Validator)
    try:
        import pymupdf as fitz
        print(f" • PyMuPDF:              {GREEN}OK{RESET} (v{fitz.__version__})")
    except ImportError:
        print(f" • PyMuPDF:              {RED}MISSING (pip install pymupdf){RESET}")
        all_healthy = False

    # 7. Notion Cloud Connection
    env = load_env(ROOT_DIR / ".env")
    notion_key = env.get("NOTION_API_KEY")
    notion_db = env.get("NOTION_DATABASE_ID")
    if notion_key and notion_db:
        try:
            schema = get_database_schema(notion_key, notion_db)
            if schema:
                props = ", ".join(list(schema.keys())[:4])
                print(f" • Notion Cloud Sync:    {GREEN}CONNECTED{RESET} (DB: {notion_db[:8]}... | Props: {props}...)")
            else:
                print(f" • Notion Cloud Sync:    {YELLOW}CONNECTED BUT SCHEMA EMPTY{RESET}")
        except Exception as e:
            print(f" • Notion Cloud Sync:    {RED}API ERROR ({e}){RESET}")
            all_healthy = False
    else:
        print(f" • Notion Cloud Sync:    {YELLOW}NOT CONFIGURED IN .env{RESET}")

    # 8. Outlook Mail / OTP Bridge
    outlook_email = env.get("OUTLOOK_EMAIL")
    outlook_pw = env.get("OUTLOOK_PASSWORD")
    if outlook_email and outlook_pw:
        print(f" • Outlook Bridge:       {GREEN}CONFIGURED{RESET} ({outlook_email})")
    else:
        print(f" • Outlook Bridge:       {YELLOW}CREDENTIALS MISSING IN .env{RESET}")

    print("\n" + "="*80)
    if all_healthy:
        print(f"{GREEN}{BOLD} ENGINE STATUS: 100% OPERATIONAL & READY TO LAUNCH{RESET}")
    else:
        print(f"{YELLOW}{BOLD} ENGINE STATUS: RUNNING WITH MINOR WARNINGS (See details above){RESET}")
    print("="*80 + "\n")
    return all_healthy

def show_tracker():
    """Displays current tracked applications from SQLite store."""
    db_path = ROOT_DIR / "data" / "applications.db"
    if not db_path.exists():
        print("[ERROR] Database not found at data/applications.db")
        return

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, company, role, status, holistic_score, submission_receipt, updated_at FROM applications ORDER BY updated_at DESC")
    rows = cur.fetchall()
    conn.close()

    print(f"\n{BOLD}AUTHORITATIVE APPLICATION TRACKER ({len(rows)} Records):{RESET}")
    print("-" * 80)
    print(f"{'STATUS':<15} | {'FIT':<4} | {'COMPANY':<22} | {'ROLE':<30}")
    print("-" * 80)
    for r in rows:
        status = r["status"]
        if status == "submitted":
            status_str = f"{GREEN}{status:<15}{RESET}"
        elif status == "prepared":
            status_str = f"{CYAN}{status:<15}{RESET}"
        elif status == "ineligible":
            status_str = f"{RED}{status:<15}{RESET}"
        else:
            status_str = f"{YELLOW}{status:<15}{RESET}"

        fit = f"{r['holistic_score']:.1f}" if r["holistic_score"] else "0.0"
        company = (r["company"] or "Unknown")[:22]
        role = (r["role"] or "AI Engineer")[:30]
        print(f"{status_str} | {fit:<4} | {company:<22} | {role:<30}")
    print("-" * 80 + "\n")

def interactive_menu():
    """Main interactive terminal cockpit."""
    while True:
        print_banner()
        print(f"{BOLD}CHOOSE AN ENGINE ACTION:{RESET}")
        print(f"  {CYAN}[1]{RESET} 🔍  {BOLD}Source Fresh Jobs{RESET}          (Firecrawl hunter: Gulf + Global ATS)")
        print(f"  {CYAN}[2]{RESET} 📊  {BOLD}Evaluate Discovered Batch{RESET}  (Score match & render chat digest cards)")
        print(f"  {CYAN}[3]{RESET} 🚀  {BOLD}Autonomous Apply (Dry-Run){RESET} (Headed Playwright: fills form & pauses)")
        print(f"  {CYAN}[4]{RESET} ⚡  {BOLD}Autonomous Apply (Live){RESET}    (Auto-fills, waits for OTP, submits & proof)")
        print(f"  {CYAN}[5]{RESET} 📬  {BOLD}Generate Outreach Dossier{RESET}  (1-Click LinkedIn notes & cold emails)")
        print(f"  {CYAN}[6]{RESET} 🔄  {BOLD}Sync Applications to Notion{RESET}(Pushes SQLite records to Notion board)")
        print(f"  {CYAN}[7]{RESET} 📋  {BOLD}View Application Tracker{RESET}   (View all tracked jobs in SQLite)")
        print(f"  {CYAN}[8]{RESET} 🧪  {BOLD}Run Resilience Test Suite{RESET}  (Execute all 9 automated tests)")
        print(f"  {CYAN}[9]{RESET} 🏥  {BOLD}System Health Diagnostics{RESET}  (Check all local engines & API tokens)")
        print(f"  {CYAN}[0]{RESET} ❌  {BOLD}Exit Engine{RESET}")
        print("-" * 80)

        choice = input(f"{BOLD}Enter choice [0-9]: {RESET}").strip()

        if choice == "1":
            print(f"\n{CYAN}Select sourcing target:{RESET}")
            print("  1. Gulf Portals (Saudi Arabia Indeed, UAE Indeed, Bayt)")
            print("  2. Global ATS Portals (Greenhouse, Lever, Ashby)")
            print("  3. All Portals")
            sub_choice = input("Target [1-3, default=3]: ").strip()
            source = "gulf" if sub_choice == "1" else ("ats" if sub_choice == "2" else "all")
            limit = input("Max jobs per query [default=10]: ").strip() or "10"
            cmd = [sys.executable, str(SCRIPTS_DIR / "firecrawl_job_hunter.py"), "--source", source, "--limit", limit]
            subprocess.run(cmd)

        elif choice == "2":
            evaluated = evaluate_batch()
            print_chat_digest(evaluated)

        elif choice == "3":
            evaluated = evaluate_batch()
            print_chat_digest(evaluated)
            target = input(f"\n{BOLD}Enter job index to dry-run (e.g. '1' or '1,3'): {RESET}").strip()
            if target:
                indices = [int(x.strip()) for x in target.split(",") if x.strip().isdigit()]
                apply_selected_jobs(indices, dry_run=True, headless=False)

        elif choice == "4":
            evaluated = evaluate_batch()
            print_chat_digest(evaluated)
            print(f"{YELLOW}{BOLD}⚠️  CONFIRMATION REQUIRED: Live Autonomous Submission Mode{RESET}")
            target = input(f"{BOLD}Enter job index to LIVE SUBMIT (e.g. '1' or '1,2'): {RESET}").strip()
            if target:
                confirm = input(f"Are you sure you want to autonomously submit to job(s) {target}? [y/N]: ").strip().lower()
                if confirm == "y":
                    indices = [int(x.strip()) for x in target.split(",") if x.strip().isdigit()]
                    apply_selected_jobs(indices, dry_run=False, headless=False)
                else:
                    print("[ABORTED] Live submission cancelled.")

        elif choice == "5":
            evaluated = evaluate_batch()
            target = input(f"\n{BOLD}Enter job index to generate outreach dossier [1-{len(evaluated)}]: {RESET}").strip()
            if target.isdigit():
                idx = int(target)
                matches = [j for j in evaluated if j["index"] == idx]
                if matches:
                    t = matches[0]
                    dossier = generate_outreach_dossier(t["company"], t["title"], jd_text=t["jd_text"], archetype=t["archetype"])
                    print_dossier(dossier)
                else:
                    print(f"[ERROR] Job index {idx} not found.")

        elif choice == "6":
            env = load_env(ROOT_DIR / ".env")
            if env.get("NOTION_API_KEY") and env.get("NOTION_DATABASE_ID"):
                print(f"\n{CYAN}[NOTION SYNC] Pushing local applications to Notion...{RESET}")
                sync_applications_to_notion(env["NOTION_API_KEY"], env["NOTION_DATABASE_ID"], root_dir=ROOT_DIR)
            else:
                print(f"[ERROR] Notion credentials missing in .env")

        elif choice == "7":
            show_tracker()

        elif choice == "8":
            cmd = [sys.executable, "-u", str(SCRIPTS_DIR / "test_pipeline_resilience.py")]
            subprocess.run(cmd)

        elif choice == "9":
            run_diagnostics()

        elif choice == "0":
            print(f"\n{GREEN}Engine shutdown cleanly. Happy hunting!{RESET}\n")
            sys.exit(0)

        else:
            print(f"{RED}Invalid option. Please choose between 0 and 9.{RESET}")

        input(f"\n{DIM}Press [Enter] to return to Cockpit Menu...{RESET}")

def main():
    parser = argparse.ArgumentParser(description="Career-Ops HITL Autonomous Application Engine Cockpit")
    parser.add_argument("--health", action="store_true", help="Run comprehensive system health diagnostics")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate discovered jobs batch and render cards")
    parser.add_argument("--source", choices=["ats", "gulf", "all"], help="Source fresh jobs via Firecrawl")
    parser.add_argument("--apply", help="Comma-separated indices to apply (e.g. '1,3' or 'all')")
    parser.add_argument("--dry-run", action="store_true", help="Visual dry-run mode (does not click submit)")
    parser.add_argument("--headless", action="store_true", help="Run Playwright browser in background headless mode")
    parser.add_argument("--outreach", type=int, help="Generate outreach dossier for specified job index")
    parser.add_argument("--sync", action="store_true", help="Sync local SQLite store to Notion database")
    parser.add_argument("--list", action="store_true", help="List all tracked applications from SQLite")
    parser.add_argument("--test", action="store_true", help="Run the 9-test pipeline resilience suite")

    args = parser.parse_args()

    # If any CLI flags provided, run non-interactively
    if args.health:
        run_diagnostics()
    elif args.test:
        cmd = [sys.executable, "-u", str(SCRIPTS_DIR / "test_pipeline_resilience.py")]
        subprocess.run(cmd)
    elif args.list:
        show_tracker()
    elif args.sync:
        env = load_env(ROOT_DIR / ".env")
        if env.get("NOTION_API_KEY") and env.get("NOTION_DATABASE_ID"):
            sync_applications_to_notion(env["NOTION_API_KEY"], env["NOTION_DATABASE_ID"], root_dir=ROOT_DIR)
        else:
            print("[ERROR] Notion credentials missing in .env")
    elif args.source:
        from firecrawl_job_hunter import discover_jobs
        discover_jobs(source=args.source, limit=10)
    elif args.outreach is not None:
        eval_file = ROOT_DIR / "data" / "evaluated_batch.json"
        if not eval_file.exists():
            evaluate_batch()
        with open(eval_file, "r", encoding="utf-8") as f:
            evaluated = json.load(f)
        matches = [j for j in evaluated if j["index"] == args.outreach]
        if matches:
            t = matches[0]
            dossier = generate_outreach_dossier(t["company"], t["title"], jd_text=t["jd_text"], archetype=t["archetype"])
            print_dossier(dossier)
        else:
            print(f"[ERROR] Job index {args.outreach} not found.")
    elif args.evaluate:
        evaluated = evaluate_batch()
        print_chat_digest(evaluated)
    elif args.apply:
        eval_file = ROOT_DIR / "data" / "evaluated_batch.json"
        if not eval_file.exists():
            evaluate_batch()
        with open(eval_file, "r", encoding="utf-8") as f:
            evaluated = json.load(f)

        if args.apply.strip().lower() == "all":
            indices = [j["index"] for j in evaluated if j.get("eligibility") == "PASS"]
        else:
            indices = [int(x.strip()) for x in args.apply.split(",") if x.strip().isdigit()]

        apply_selected_jobs(indices, dry_run=args.dry_run, headless=args.headless)
    else:
        # Launch Interactive Menu
        interactive_menu()

if __name__ == "__main__":
    main()
