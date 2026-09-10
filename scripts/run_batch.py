#!/usr/bin/env python3
"""
run_batch.py
Unified Orchestrator for HITL Job Application Automation:
- Bridges Firecrawl discovery with sub-second ATS resume tailoring and autonomous browser application
- Renders concise, decision-ready job match cards for human review
- Supports:
    python scripts/run_batch.py --evaluate         (Evaluates discovered jobs and outputs digest)
    python scripts/run_batch.py --apply 1,3        (Tailors and auto-submits approved jobs via headed browser)
    python scripts/run_batch.py --apply 1 --dry-run (Fills form, pauses on screen, verifies without submitting)
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

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

from fast_ats_tailor import (
    run_fast_tailor,
    extract_keywords_from_text,
    detect_archetype,
    score_ats_match,
    load_canonical_profile,
    get_candidate_all_skills
)
from autonomous_browser_agent import AIBrowserAgent

def load_discovered_jobs() -> List[Dict[str, Any]]:
    batch_file = ROOT_DIR / "data" / "discovered_jobs.json"
    if not batch_file.exists():
        return []
    with open(batch_file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_evaluated_batch(evaluated_jobs: List[Dict[str, Any]]):
    eval_file = ROOT_DIR / "data" / "evaluated_batch.json"
    with open(eval_file, "w", encoding="utf-8") as f:
        json.dump(evaluated_jobs, f, indent=2)

def evaluate_batch() -> List[Dict[str, Any]]:
    jobs = load_discovered_jobs()
    if not jobs:
        print("[NOTICE] No jobs found in data/discovered_jobs.json.")
        return []

    profile = load_canonical_profile(ROOT_DIR)
    candidate_skills = get_candidate_all_skills(profile)

    print(f"\n[EVALUATE] Analyzing {len(jobs)} discovered jobs against canonical profile...")
    evaluated = []

    for idx, j in enumerate(jobs, 1):
        url = j.get("url", "")
        title = j.get("title", "")
        company = j.get("company", "")
        jd_text = j.get("markdown") or j.get("snippet") or f"{title} at {company}"

        # Keyword and archetype extraction
        kws = extract_keywords_from_text(f"{title}\n{jd_text}")
        archetype = detect_archetype(jd_text)
        score, matched_kws, missing_kws = score_ats_match(kws, candidate_skills)

        # Eligibility check
        eligibility = "PASS"
        notes = "Meets experience & location/remote profile."
        text_lower = jd_text.lower()
        if "security clearance" in text_lower or "us citizen only" in text_lower:
            eligibility = "FAIL"
            notes = "Requires US Security Clearance / US Citizenship."
        elif "8+ years" in text_lower or "10+ years" in text_lower:
            eligibility = "FAIL"
            notes = "Requires > 8 years mandatory experience (exceeds candidate profile)."

        eval_item = {
            "index": idx,
            "url": url,
            "title": title,
            "company": company,
            "score": score,
            "archetype": archetype,
            "eligibility": eligibility,
            "eligibility_notes": notes,
            "matched_keywords": list(matched_kws)[:6],
            "jd_text": jd_text
        }
        evaluated.append(eval_item)

    # Sort by score descending
    evaluated.sort(key=lambda x: (x["eligibility"] == "PASS", x["score"]), reverse=True)
    
    # Re-index
    for i, item in enumerate(evaluated, 1):
        item["index"] = i

    save_evaluated_batch(evaluated)
    return evaluated

def print_chat_digest(evaluated_jobs: List[Dict[str, Any]]):
    """Outputs high-clarity markdown cards formatted for the chat interface."""
    print("\n" + "="*70)
    print(f"🎯 BATCH DIGEST: {len(evaluated_jobs)} JOBS EVALUATED (Top Matches Ready for Review)")
    print("="*70 + "\n")

    for j in evaluated_jobs:
        if j["eligibility"] == "FAIL":
            continue

        stars = "⭐⭐⭐⭐⭐" if j["score"] >= 80 else ("⭐⭐⭐⭐" if j["score"] >= 65 else "⭐⭐⭐")
        print(f"### [{j['index']}] {j['title']} — {j['company']}")
        print(f"- **Portal**: `{j['url'][:55]}...`")
        print(f"- **Match Score**: **{j['score']}%** ({j['archetype'].upper()}) {stars}")
        print(f"- **Key Overlap**: {', '.join(j['matched_keywords']) if j['matched_keywords'] else 'Standard AI/ML Stack'}")
        print(f"- **Eligibility**: `{j['eligibility']}` ({j['eligibility_notes']})")
        print(f"- **Action**: Say `Apply to {j['index']}` or `Apply all`\n")

    print("="*70)
    print("👉 To apply, reply in chat: 'Apply to #1, #3' or run: python scripts/run_batch.py --apply 1,3")
    print("="*70 + "\n")

def apply_selected_jobs(indices: List[int], dry_run: bool = False, headless: bool = False):
    eval_file = ROOT_DIR / "data" / "evaluated_batch.json"
    if not eval_file.exists():
        print("[ERROR] No evaluated batch found. Run --evaluate first.")
        return

    with open(eval_file, "r", encoding="utf-8") as f:
        evaluated = json.load(f)

    job_map = {j["index"]: j for j in evaluated}
    targets = [job_map[i] for i in indices if i in job_map]

    if not targets:
        print(f"[WARN] No valid jobs matching indices: {indices}")
        return

    print(f"\n[ORCHESTRATE] Processing {len(targets)} approved job applications...")

    browser_agent = AIBrowserAgent(headed=not headless, dry_run=dry_run)

    for j in targets:
        print("\n" + "#"*65)
        print(f"--> PREPARING APPLICATION FOR: [{j['index']}] {j['title']} at {j['company']}")
        print("#"*65)

        # 1. Compile Tailored ATS Resume
        print("\n[STAGE 1] Compiling tailored ATS resume PDF via fast_ats_tailor...")
        tailor_res = run_fast_tailor(
            company=j["company"],
            role=j["title"],
            jd_text=j["jd_text"],
            focus=j["archetype"] if j["archetype"] != "auto" else None
        )

        if not tailor_res.get("success"):
            print(f"[FAIL] Tailoring failed: {tailor_res.get('error')}")
            continue

        pdf_path = Path(tailor_res["pdf_path"])
        app_id = tailor_res["application_id"]
        bundle_folder = Path(tailor_res["bundle_dir"])
        screener_answers = tailor_res.get("screener_answers", {})

        print(f"[READY] Tailored PDF: {pdf_path.name} ({tailor_res['page_count']} page)")

        # Generate Deep Outreach Dossier (LinkedIn + Executive Email)
        from deep_reach import generate_outreach_dossier
        dossier = generate_outreach_dossier(
            company=j["company"],
            role=j["title"],
            jd_text=j["jd_text"],
            archetype=j["archetype"]
        )
        dossier_path = bundle_folder / "outreach_dossier.json"
        with open(dossier_path, "w", encoding="utf-8") as f:
            json.dump(dossier, f, indent=2)
        print(f"[DOSSIER] Generated multi-channel outreach assets: {dossier_path.name}")

        # Mark URL as visited in SQLite
        from db_manager import mark_url_visited
        mark_url_visited(j["url"], company=j["company"], role=j["title"])

        # 2. Launch Autonomous Browser and Submit
        print("\n[STAGE 2] Launching Autonomous Browser Submitter...")
        submit_res = browser_agent.run_submission(
            job_url=j["url"],
            company=j["company"],
            role=j["title"],
            pdf_path=pdf_path,
            app_id=app_id,
            screener_answers=screener_answers,
            bundle_folder=bundle_folder
        )

        if submit_res.get("success"):
            print(f"\n[DONE] Successfully processed {j['title']} at {j['company']}!")
            print(f"Receipt: {submit_res.get('receipt_path')}")
            print(f"Outreach Dossier: {dossier_path}")
        else:
            print(f"\n[FAIL] Submission failed: {submit_res.get('error')}")

def main():
    parser = argparse.ArgumentParser(description="Career-Ops Batch Application Orchestrator")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate current discovered jobs and output digest")
    parser.add_argument("--apply", default="", help="Comma-separated job indices to apply (e.g. '1,3,5' or 'all')")
    parser.add_argument("--outreach", type=int, default=None, help="Display deep research and outreach dossier for job index")
    parser.add_argument("--dry-run", action="store_true", help="Fill form, visually pause, but skip clicking submit")
    parser.add_argument("--headless", action="store_true", help="Run without visible browser UI")
    args = parser.parse_args()

    if args.outreach is not None:
        eval_file = ROOT_DIR / "data" / "evaluated_batch.json"
        if not eval_file.exists():
            evaluate_batch()
        with open(eval_file, "r", encoding="utf-8") as f:
            evaluated = json.load(f)
        targets = [j for j in evaluated if j["index"] == args.outreach]
        if targets:
            from deep_reach import generate_outreach_dossier, print_dossier
            t = targets[0]
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
        evaluated = evaluate_batch()
        print_chat_digest(evaluated)

if __name__ == "__main__":
    main()

