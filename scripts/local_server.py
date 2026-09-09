#!/usr/bin/env python3
"""
local_server.py
Career-Ops Local Command Hub & Browser Extension Bridge:
- Runs a lightweight HTTP API server on http://127.0.0.1:8765
- Connects the browser extension directly to Antigravity's ATS engine
- Ingests job descriptions from active browser tabs
- Tailors resumes in sub-second speed (< 1s) via fast_ats_tailor.py
- Updates SQLite data/applications.db and syncs to Notion
- Writes live context to job_research/current_active_job.json and active_session_log.md
- Serves action triggers (open PDF, open folder, autofill form)
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict, Any
import re
import sqlite3

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from fast_ats_tailor import (
    run_fast_tailor, load_canonical_profile, extract_keywords_from_text,
    detect_archetype, score_ats_match, get_candidate_all_skills
)
from sync_to_notion import sync_applications_to_notion, load_env
from db_manager import set_application_status, export_markdown_tracker

HOST = "127.0.0.1"
PORT = 8765

ACTIVE_JOB_FILE = ROOT_DIR / "job_research" / "current_active_job.json"
LIVE_FEED_FILE = ROOT_DIR / "job_research" / "live_feed.jsonl"
SESSION_LOG_FILE = ROOT_DIR / "job_research" / "active_session_log.md"

def find_existing_job(url: Optional[str] = None, company: Optional[str] = None, role: Optional[str] = None) -> Optional[dict]:
    """Checks if a job URL or role/company has already been evaluated/tailored/submitted."""
    db_file = ROOT_DIR / "data" / "applications.db"
    if not db_file.exists():
        return None

    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    row = None

    # 1. Match by source_url or canonical_url (normalize URL: remove query string & trailing slash)
    if url:
        parsed_u = urlparse(url)
        clean_url = f"{parsed_u.scheme}://{parsed_u.netloc}{parsed_u.path}".rstrip("/")
        cur.execute(
            "SELECT * FROM applications WHERE source_url = ? OR canonical_url = ? OR source_url LIKE ? OR canonical_url LIKE ? ORDER BY updated_at DESC", 
            (url, url, f"{clean_url}%", f"{clean_url}%")
        )
        row = cur.fetchone()

    # 2. Match by company and role
    if not row and role:
        c_clean = (company or "").strip()
        r_clean = (role or "").strip()
        if c_clean and c_clean.lower() not in ["target employer", "unknown", ""]:
            cur.execute("SELECT * FROM applications WHERE LOWER(company) = LOWER(?) AND LOWER(role) = LOWER(?) ORDER BY updated_at DESC", (c_clean, r_clean))
            row = cur.fetchone()
        if not row:
            cur.execute("SELECT * FROM applications WHERE LOWER(role) = LOWER(?) ORDER BY updated_at DESC", (r_clean,))
            row = cur.fetchone()

    # 3. Match by role keywords/slug if still not found
    if not row and role:
        role_slug = re.sub(r"[^\w-]", "", role.lower().replace(" ", "-"))
        if len(role_slug) > 3:
            cur.execute("SELECT * FROM applications WHERE id LIKE ? ORDER BY updated_at DESC", (f"%{role_slug}%",))
            row = cur.fetchone()

    conn.close()

    if not row:
        return None

    d = dict(row)
    app_id = d["id"]

    # Locate bundle directory
    bundle_path = None
    if d.get("folder_path") and Path(d["folder_path"]).exists():
        bundle_path = Path(d["folder_path"])
    else:
        app_dirs = list((ROOT_DIR / "applications").glob(f"*{app_id}*"))
        if not app_dirs and role:
            role_slug = re.sub(r"[^\w-]", "", role.lower().replace(" ", "-"))
            app_dirs = list((ROOT_DIR / "applications").glob(f"*{role_slug}*"))
        if app_dirs:
            bundle_path = app_dirs[0]

    manifest = {}
    screener_answers = {}
    pdf_path = None
    if bundle_path and bundle_path.exists():
        man_file = bundle_path / "submission_manifest.json"
        if man_file.exists():
            try:
                with open(man_file, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
            except Exception:
                pass
        
        screener_file = bundle_path / "block_h_screener_answers.json"
        if screener_file.exists():
            try:
                with open(screener_file, "r", encoding="utf-8") as f:
                    screener_answers = json.load(f)
            except Exception:
                pass

        pdf_file = bundle_path / "resume.pdf"
        if pdf_file.exists():
            pdf_path = str(pdf_file.resolve())

    # Fallback to current active job if screener answers missing
    if not screener_answers and ACTIVE_JOB_FILE.exists():
        try:
            with open(ACTIVE_JOB_FILE, "r", encoding="utf-8") as f:
                act = json.load(f)
            if act.get("role") == d.get("role"):
                screener_answers = act.get("screener_answers", {})
        except Exception:
            pass

    score = manifest.get("ats_match_percentage")
    if score is None:
        score = round(d.get("holistic_score", 4.0) * 20.0, 1)

    return {
        "id": app_id,
        "company": d.get("company") or manifest.get("company", "Target Employer"),
        "role": d.get("role") or manifest.get("role", "AI Engineer"),
        "status": d.get("status", "prepared"),
        "submission_receipt": d.get("submission_receipt"),
        "submitted_at": d.get("submitted_at"),
        "source_url": d.get("source_url") or url,
        "ats_score": score,
        "archetype": manifest.get("archetype", "GENERAL"),
        "matched_keywords": manifest.get("matched_keywords", []),
        "missing_keywords": manifest.get("missing_keywords", []),
        "bundle_dir": str(bundle_path.resolve()) if bundle_path else "",
        "pdf_path": pdf_path or (str((bundle_path / "resume.pdf").resolve()) if bundle_path else ""),
        "screener_answers": screener_answers
    }

def update_session_log(job_data: dict, result: dict):
    """Updates human-readable Markdown log for Antigravity chat inspection."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    company = job_data.get("company", "Unknown")
    role = job_data.get("role", "Unknown")
    url = job_data.get("url", "")
    score = result.get("ats_score", 0.0)
    archetype = result.get("archetype", "GENERAL").upper()
    pdf_path = result.get("pdf_path", "")
    matched = ", ".join(result.get("matched_keywords", []))
    missing = ", ".join(result.get("missing_keywords", [])) if result.get("missing_keywords") else "None"
    
    screener = result.get("screener_answers", {})
    tech_pitch = screener.get("technical_summary", "")

    log_content = f"""# Active Job Session Log

> **Current Status**: Application Prepared & Synced to Antigravity
> **Last Updated**: {timestamp}

## Active Target Role
* **Company**: **{company}**
* **Role**: **{role}**
* **Job URL**: [{url}]({url})
* **Archetype Focus**: `{archetype}`
* **ATS Match Score**: **{score}%**
* **Compiled PDF**: [`{pdf_path}`](file:///{pdf_path.replace(os.sep, '/')})

### Keyword Breakdown
* **Matched Skills**: {matched}
* **Missing / Bonus**: {missing}

---

## Block H Screener Answers (Ready for ATS Form)

### Technical Pitch
{tech_pitch}

### Work Authorization
{screener.get('work_authorization', '')}

### Experience Summary
{screener.get('years_experience', '')}

---
*Generated by Career-Ops Local Command Hub Bridge*
"""
    with open(SESSION_LOG_FILE, "w", encoding="utf-8") as f:
        f.write(log_content)

class CareerOpsBridgeHandler(BaseHTTPRequestHandler):
    def _respond_json(self, status_code: int, data: dict):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/health":
            active_info = {}
            if ACTIVE_JOB_FILE.exists():
                try:
                    with open(ACTIVE_JOB_FILE, "r", encoding="utf-8") as f:
                        active_info = json.load(f)
                except Exception:
                    pass

            self._respond_json(200, {
                "status": "online",
                "service": "Career-Ops Command Hub",
                "version": "1.0.0",
                "active_job": active_info
            })

        elif parsed.path == "/api/active-job":
            if ACTIVE_JOB_FILE.exists():
                try:
                    with open(ACTIVE_JOB_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self._respond_json(200, data)
                except Exception as e:
                    self._respond_json(500, {"error": str(e)})
            else:
                self._respond_json(404, {"error": "No active job"})

        elif parsed.path == "/api/pdf":
            query_params = parse_qs(parsed.query)
            pdf_path_param = query_params.get("path", [None])[0]
            app_id_param = query_params.get("id", [None])[0]
            target_pdf = None

            if pdf_path_param:
                p = Path(pdf_path_param).resolve()
                if p.exists() and p.is_file() and p.suffix.lower() == ".pdf":
                    target_pdf = p
            elif app_id_param:
                found = list((ROOT_DIR / "applications").glob(f"*{app_id_param}*/resume.pdf"))
                if found and found[0].exists():
                    target_pdf = found[0].resolve()

            if target_pdf and target_pdf.exists():
                try:
                    with open(target_pdf, "rb") as f:
                        pdf_bytes = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/pdf")
                    self.send_header("Content-Disposition", f'inline; filename="{target_pdf.name}"')
                    self.send_header("Content-Length", str(len(pdf_bytes)))
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(pdf_bytes)
                except Exception as e:
                    self._respond_json(500, {"error": f"Failed to read PDF: {str(e)}"})
            else:
                self._respond_json(404, {"error": "PDF not found", "path": pdf_path_param or app_id_param})

        else:
            self._respond_json(404, {"error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)

        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len) if content_len > 0 else b"{}"

        try:
            payload = json.loads(post_body.decode("utf-8"))
        except Exception:
            payload = {}

        if parsed.path == "/api/check-job":
            url = payload.get("url", "").strip()
            company = payload.get("company", "").strip()
            role = payload.get("role", "").strip()

            existing = find_existing_job(url=url, company=company, role=role)
            if existing:
                self._respond_json(200, {
                    "exists": True,
                    "application": existing
                })
            else:
                self._respond_json(200, {
                    "exists": False
                })

        elif parsed.path == "/api/evaluate":
            company = payload.get("company", "").strip() or "Target Employer"
            role = payload.get("role", "").strip() or "AI Engineer"
            jd_text = payload.get("jd_text", "").strip()
            focus = payload.get("focus", "auto")

            profile = load_canonical_profile(ROOT_DIR)
            candidate_skills = get_candidate_all_skills(profile)
            extracted_kws = extract_keywords_from_text(jd_text)
            archetype = detect_archetype(jd_text, explicit_focus=None if focus == "auto" else focus)
            ats_score, matched_kws, missing_kws = score_ats_match(extracted_kws, candidate_skills)

            self._respond_json(200, {
                "success": True,
                "company": company,
                "role": role,
                "ats_score": ats_score,
                "archetype": archetype,
                "matched_keywords": matched_kws,
                "missing_keywords": missing_kws
            })

        elif parsed.path == "/api/tailor":
            company = payload.get("company", "").strip() or "Target Employer"
            role = payload.get("role", "").strip() or "AI Engineer"
            jd_text = payload.get("jd_text", "").strip()
            source_url = payload.get("url", "").strip()
            focus = payload.get("focus", "auto")
            sync_notion = payload.get("sync", True)

            if not jd_text:
                jd_text = f"{role} at {company}. Experience with Python, machine learning, and AI."

            focus_param = None if focus == "auto" else focus

            # Run the fast ATS tailoring engine
            t0 = time.time()
            res = run_fast_tailor(
                company=company,
                role=role,
                jd_text=jd_text,
                source_url=source_url,
                focus=focus_param,
                sync_to_notion_flag=sync_notion,
                benchmark=True
            )

            if res.get("success"):
                # Persist active job session
                active_record = {
                    "timestamp": datetime.now().isoformat(),
                    "company": company,
                    "role": role,
                    "url": source_url,
                    "ats_score": res.get("ats_score"),
                    "archetype": res.get("archetype"),
                    "matched_keywords": res.get("matched_keywords"),
                    "missing_keywords": res.get("missing_keywords"),
                    "pdf_path": res.get("pdf_path"),
                    "bundle_dir": res.get("bundle_dir"),
                    "screener_answers": res.get("screener_answers")
                }
                with open(ACTIVE_JOB_FILE, "w", encoding="utf-8") as f:
                    json.dump(active_record, f, indent=2)

                with open(LIVE_FEED_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(active_record) + "\n")

                update_session_log(active_record, res)

                self._respond_json(200, {
                    "success": True,
                    "application_id": res["application_id"],
                    "ats_score": res["ats_score"],
                    "archetype": res["archetype"],
                    "matched_keywords": res["matched_keywords"],
                    "missing_keywords": res["missing_keywords"],
                    "pdf_path": res["pdf_path"],
                    "bundle_dir": res["bundle_dir"],
                    "screener_answers": res["screener_answers"],
                    "execution_ms": res["timings"]["total_execution_ms"],
                    "notion_synced": sync_notion
                })

            else:
                self._respond_json(500, {"success": False, "error": res.get("error")})

        elif parsed.path == "/api/open-pdf":
            pdf_path = payload.get("pdf_path", "")
            p = Path(pdf_path).resolve() if pdf_path else None
            if p and p.exists() and p.is_file():
                if sys.platform == "win32":
                    try:
                        os.startfile(str(p))
                    except Exception as e:
                        subprocess.Popen(["cmd", "/c", "start", "", str(p)], shell=True)
                else:
                    subprocess.Popen(["xdg-open", str(p)])
                self._respond_json(200, {"success": True, "path": str(p)})
            else:
                self._respond_json(400, {"error": "File does not exist", "path": pdf_path})

        elif parsed.path == "/api/open-folder":
            bundle_dir = payload.get("bundle_dir", "")
            p = Path(bundle_dir).resolve() if bundle_dir else None
            if p and p.exists() and p.is_dir():
                if sys.platform == "win32":
                    try:
                        subprocess.Popen(["explorer.exe", str(p)])
                    except Exception:
                        os.startfile(str(p))
                else:
                    subprocess.Popen(["xdg-open", str(p)])
                self._respond_json(200, {"success": True, "path": str(p)})
            else:
                self._respond_json(400, {"error": "Directory does not exist", "path": bundle_dir})

        elif parsed.path == "/api/sync-notion":
            env = load_env(ROOT_DIR / ".env")
            if env.get("NOTION_API_KEY") and env.get("NOTION_DATABASE_ID"):
                sync_res = sync_applications_to_notion(env["NOTION_API_KEY"], env["NOTION_DATABASE_ID"], root_dir=ROOT_DIR)
                self._respond_json(200, sync_res)
        elif parsed.path == "/api/mark-applied":
            app_id = payload.get("application_id", "")
            receipt = payload.get("receipt", "").strip() or f"DIRECT-SUBMIT-{datetime.now().strftime('%Y%m%d%H%M')}"
            
            try:
                set_application_status(app_id, "submitted", submission_receipt=receipt)
                tracker_file = ROOT_DIR / "job_research" / "active_application_tracker.md"
                export_markdown_tracker(tracker_file)
                
                # Update active job file status
                if ACTIVE_JOB_FILE.exists():
                    try:
                        with open(ACTIVE_JOB_FILE, "r", encoding="utf-8") as f:
                            act = json.load(f)
                        act["status"] = "submitted"
                        act["receipt"] = receipt
                        with open(ACTIVE_JOB_FILE, "w", encoding="utf-8") as f:
                            json.dump(act, f, indent=2)
                    except Exception:
                        pass
                
                # Sync to Notion
                env = load_env(ROOT_DIR / ".env")
                if env.get("NOTION_API_KEY") and env.get("NOTION_DATABASE_ID"):
                    sync_applications_to_notion(env["NOTION_API_KEY"], env["NOTION_DATABASE_ID"], root_dir=ROOT_DIR)

                self._respond_json(200, {
                    "success": True,
                    "status": "submitted",
                    "receipt": receipt
                })
            except Exception as e:
                self._respond_json(500, {"success": False, "error": str(e)})

        else:
            self._respond_json(404, {"error": "Not found"})

def run_server(port=PORT):
    server = HTTPServer((HOST, port), CareerOpsBridgeHandler)
    print(f"[Career-Ops Hub] Server running at http://{HOST}:{port}")
    print(f" -> Live session log: {SESSION_LOG_FILE}")
    print(f" -> Ready for browser extension requests...\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Career-Ops Hub] Server stopped.")
        server.server_close()

if __name__ == "__main__":
    run_server()
