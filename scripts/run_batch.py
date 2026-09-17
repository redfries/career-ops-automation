import os
import sys
import sqlite3
import argparse
import subprocess
from pathlib import Path

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = 'data/jobs.db'

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def show_status():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT count(*) FROM jobs")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT status, count(*) FROM jobs GROUP BY status ORDER BY count(*) DESC")
    status_counts = cur.fetchall()
    
    print("\n" + "=" * 55)
    print("📊 CAREER-OPS STATEFUL PIPELINE STATUS COCKPIT")
    print("=" * 55)
    print(f"Total Database Jobs: {total}")
    print("-" * 55)
    for st, count in status_counts:
        icon = {
            'shortlisted': '⭐',
            'tailored': '📝',
            'applied': '🎉',
            'needs_manual_review': '⚠️',
            'evaluated': '🔍',
            'low_fit': '📉',
            'out_of_region': '🌐'
        }.get(st, '▪️')
        print(f"  {icon} {st:<22}: {count:>5}")
    print("-" * 55)

    # Show top ready-to-tailor shortlisted jobs
    cur.execute("""
        SELECT id, company, title, location, match_score 
        FROM jobs 
        WHERE status = 'shortlisted' 
        ORDER BY match_score DESC 
        LIMIT 5
    """)
    shortlisted_jobs = cur.fetchall()
    if shortlisted_jobs:
        print("\n👉 NEXT 5 SHORTLISTED JOBS READY FOR TAILORING:")
        for jid, comp, title, loc, score in shortlisted_jobs:
            print(f"   [{jid}] {comp:<22} | {title:<30} | {score} pts")

    # Show tailored jobs ready to apply
    cur.execute("""
        SELECT id, company, title, application_folder 
        FROM jobs 
        WHERE status = 'tailored' 
        LIMIT 5
    """)
    tailored_jobs = cur.fetchall()
    if tailored_jobs:
        print("\n🚀 NEXT TAILORED JOBS READY TO APPLY:")
        for jid, comp, title, folder in tailored_jobs:
            print(f"   [{jid}] {comp:<22} | {title:<30}")
            print(f"         📁 {folder}")

    conn.close()
    print("=" * 55 + "\n")

def run_tailor(limit: int):
    print(f"\n🎯 Launching Full 7-Stage Pipeline Orchestrator for top {limit} shortlisted job(s)...")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, company, title 
        FROM jobs 
        WHERE status = 'shortlisted' 
        ORDER BY match_score DESC 
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("⚠️ No shortlisted jobs found ready to process.")
        return

    for jid, comp, title in rows:
        print(f"\n>>> Running Pipeline for: {comp} - {title} (#{jid})")
        cmd = [sys.executable, "scripts/pipeline_orchestrator.py", "--job-id", str(jid)]
        res = subprocess.run(cmd)
        if res.returncode != 0:
            print(f"❌ Pipeline failed for job #{jid}. Halting batch to preserve integrity.")
            break

def run_apply(limit: int, mode: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, application_folder 
        FROM jobs 
        WHERE status = 'tailored' AND application_folder IS NOT NULL 
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("\n⚠️ No tailored jobs found ready to apply. Run --tailor first!")
        return

    print(f"\n🚀 Launching Browser Submitter Loop for {len(rows)} job(s) in [{mode.upper()}] mode...")
    for jid, folder in rows:
        if not folder or not os.path.exists(folder):
            print(f"⚠️ Folder {folder} not found on disk, skipping.")
            continue
        
        cmd = [sys.executable, "scripts/browser_apply_engine.py", "--folder", folder, "--mode", mode]
        proc = subprocess.run(cmd)
        if proc.returncode != 0:
            print(f"⚠️ Submitter returned non-zero code for job {jid}. Proceeding smoothly to next job...")

def main():
    parser = argparse.ArgumentParser(description="Career-Ops Unified Batch & Pipeline Cockpit")
    parser.add_argument("--status", action="store_true", help="Display status of database and queues")
    parser.add_argument("--tailor", type=int, metavar="N", help="Tailor packages for next N shortlisted jobs")
    parser.add_argument("--apply", type=int, metavar="N", help="Apply to next N tailored jobs")
    parser.add_argument("--mode", type=str, choices=["assisted", "dry-run", "auto"], default="assisted", help="Apply execution mode")
    parser.add_argument("--tailor-job", type=str, help="Tailor a specific job ID")
    parser.add_argument("--apply-job", type=str, help="Apply to a specific job ID")
    parser.add_argument("--email", type=str, help="Send tailored outreach email for a specific job ID")
    parser.add_argument("--to", type=str, help="Recipient email address for outreach")
    parser.add_argument("--force", action="store_true", help="Force resend email even if already dispatched")

    parser.add_argument("--confirm-applied", type=str, metavar="JOB_ID", help="Safely record verified submission in DB")
    parser.add_argument("--notes", type=str, help="Application notes for confirm-applied")

    args = parser.parse_args()

    if args.status or len(sys.argv) == 1:
        show_status()
    elif args.confirm_applied:
        cmd = [sys.executable, "scripts/pipeline_orchestrator.py", "--confirm-applied", args.confirm_applied]
        if args.notes:
            cmd.extend(["--notes", args.notes])
        subprocess.run(cmd)
    elif args.tailor:
        run_tailor(args.tailor)
    elif args.tailor_job:
        cmd = [sys.executable, "scripts/pipeline_orchestrator.py", "--job-id", args.tailor_job]
        subprocess.run(cmd)
    elif args.apply:
        run_apply(args.apply, args.mode)
    elif args.apply_job:
        cmd = [sys.executable, "scripts/browser_apply_engine.py", "--job-id", args.apply_job, "--mode", args.mode]
        subprocess.run(cmd)
    elif args.email:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT application_folder FROM jobs WHERE id = ?", (args.email,))
        row = cur.fetchone()
        conn.close()

        if not row or not row[0]:
            print(f"⚠️ Application folder not found in database for job {args.email}. Run --tailor-job {args.email} first!")
        else:
            folder = row[0]
            cmd = [sys.executable, "scripts/send_resend_email.py", "--app-dir", folder]
            if args.to:
                cmd.extend(["--to", args.to])
            if args.force:
                cmd.append("--force")
            subprocess.run(cmd)

if __name__ == "__main__":
    main()
