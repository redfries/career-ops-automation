#!/usr/bin/env python3
"""
firecrawl_job_hunter.py
Multi-Portal Firecrawl Job Hunter & Deduplication Engine:
- Searches top Global ATS portals (Greenhouse, Lever, Ashby)
- Searches top Gulf / Middle East portals (sa.indeed.com, ae.indeed.com, bayt.com, naukrigulf.com)
- Targets Saudi Arabia (Riyadh, Dhahran, Khobar, Jeddah), UAE (Dubai, Abu Dhabi), and Global Remote
- Enforces permanent SQLite deduplication (data/applications.db) BEFORE scraping to conserve Firecrawl credits
- Automatically extracts direct recruiter/hiring emails from job postings
- Marks visited URLs in SQLite so they are never revisited
"""

import os
import sys
import re
import json
import sqlite3
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import urllib.request
import urllib.parse

# Ensure scripts directory in sys.path
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

from db_manager import is_url_visited, mark_url_visited

def load_env_file():
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()

def get_db_urls() -> set:
    """Returns a set of canonical and source URLs already recorded in SQLite."""
    db_path = ROOT_DIR / "data" / "applications.db"
    if not db_path.exists():
        return set()
    urls = set()
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT source_url, canonical_url FROM applications")
        for row in cursor.fetchall():
            if row[0]:
                urls.add(row[0].strip().rstrip("/"))
            if row[1]:
                urls.add(row[1].strip().rstrip("/"))
        conn.close()
    except Exception as e:
        print(f"[WARN] Error reading DB URLs: {e}")
    return urls

def extract_company_from_url(url: str, title: str = "") -> str:
    """Extracts company slug or name from common ATS and Gulf portal URL patterns."""
    # Lever
    m_lever = re.search(r"jobs\.lever\.co/([^/]+)", url)
    if m_lever:
        return m_lever.group(1).replace("-", " ").title()
    
    # Greenhouse
    m_gh = re.search(r"(?:boards|job-boards)\.greenhouse\.io/([^/]+)", url)
    if m_gh:
        return m_gh.group(1).replace("-", " ").title()
        
    # Ashby
    m_ashby = re.search(r"jobs\.ashbyhq\.com/([^/]+)", url)
    if m_ashby:
        return m_ashby.group(1).replace("-", " ").title()

    # Bayt: bayt.com/en/saudi-arabia/jobs/<company>-jobs/
    m_bayt = re.search(r"bayt\.com/en/[^/]+/jobs/([^/]+)-jobs", url)
    if m_bayt:
        return m_bayt.group(1).replace("-", " ").title()

    # Title heuristics: "AI Engineer at XYZ" or "Company - Role"
    if " at " in title:
        return title.split(" at ")[-1].strip()
    if " — " in title:
        return title.split(" — ")[-1].strip()
    if " - " in title:
        parts = title.split(" - ")
        if len(parts) >= 2:
            return parts[1].strip()

    return "Target Employer"

def extract_contact_email(text: str) -> Optional[str]:
    """Finds direct recruiter or hiring emails in job description text."""
    if not text:
        return None
    matches = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    ignore_domains = {"example.com", "indeed.com", "lever.co", "greenhouse.io", "ashbyhq.com", "bayt.com"}
    for email_found in matches:
        domain = email_found.split("@")[-1].lower()
        if domain not in ignore_domains and not domain.endswith(".png") and not domain.endswith(".jpg"):
            return email_found
    return None

def call_firecrawl_api(endpoint: str, payload: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    url = f"https://api.firecrawl.dev/v1/{endpoint.lstrip('/')}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"[ERROR] Firecrawl API {e.code}: {body}")
        return {"success": False, "error": f"HTTP {e.code}: {body}"}
    except Exception as e:
        print(f"[ERROR] Network error contacting Firecrawl: {e}")
        return {"success": False, "error": str(e)}

def get_preset_queries(source: str = "all") -> List[str]:
    """Returns tailored Firecrawl search queries for ATS and Gulf portals."""
    gulf_queries = [
        # Saudi Arabia Indeed
        'site:sa.indeed.com ("AI Engineer" OR "Machine Learning Engineer" OR "Computer Vision") ("Riyadh" OR "Dhahran" OR "Khobar" OR "Jeddah" OR "Saudi Arabia")',
        # UAE Indeed
        'site:ae.indeed.com ("AI Engineer" OR "Machine Learning Engineer" OR "Computer Vision") ("Dubai" OR "Abu Dhabi" OR "UAE")',
        # Bayt.com Middle East
        'site:bayt.com/en ("AI Engineer" OR "Machine Learning" OR "Computer Vision") ("Saudi Arabia" OR "UAE" OR "Riyadh" OR "Dubai")',
        # Naukrigulf
        'site:naukrigulf.com ("AI Engineer" OR "Machine Learning Engineer") ("Saudi Arabia" OR "UAE" OR "Dubai")'
    ]

    ats_queries = [
        # Greenhouse, Lever, Ashby - Saudi & UAE & Remote
        '(site:jobs.lever.co OR site:boards.greenhouse.io OR site:jobs.ashbyhq.com) '
        '("AI Engineer" OR "Machine Learning Engineer" OR "Computer Vision" OR "Generative AI") '
        '("Saudi Arabia" OR "Riyadh" OR "UAE" OR "Dubai" OR "Remote")'
    ]

    if source == "gulf":
        return gulf_queries
    elif source == "ats":
        return ats_queries
    else:
        return ats_queries + gulf_queries

def discover_jobs(
    query: Optional[str] = None,
    source: str = "all",
    limit: int = 10,
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    api_key = api_key or os.environ.get("FIRECRAWL_API_KEY")
    known_urls = get_db_urls()
    print(f"[DEDUPE] Loaded {len(known_urls)} existing application/visited URLs from SQLite.")

    queries = [query] if query else get_preset_queries(source)
    all_fresh_jobs = []

    for q in queries:
        print(f"\n[SEARCH] Running Firecrawl query: {q[:70]}...")
        if not api_key:
            print("[NOTICE] FIRECRAWL_API_KEY not found in .env. Use Antigravity MCP tool calls directly.")
            break

        payload = {"query": q, "limit": limit}
        res = call_firecrawl_api("search", payload, api_key)
        if not res.get("success"):
            print(f"[WARN] Search query failed: {res.get('error')}")
            continue

        data_items = res.get("data", {}).get("web", []) or res.get("data", [])
        for item in data_items:
            url = item.get("url", "").strip().rstrip("/")
            if not url or url in known_urls:
                continue

            title = item.get("title", "")
            company = extract_company_from_url(url, title)
            snippet = item.get("description", "")
            markdown = item.get("markdown", "")
            contact_email = extract_contact_email(f"{snippet} {markdown}")

            job_obj = {
                "url": url,
                "title": title,
                "company": company,
                "snippet": snippet,
                "markdown": markdown,
                "contact_email": contact_email
            }
            all_fresh_jobs.append(job_obj)
            known_urls.add(url)
            # Mark visited immediately so subsequent queries don't duplicate
            mark_url_visited(url, company=company, role=title)

    print(f"\n[DISCOVERY COMPLETE] Found {len(all_fresh_jobs)} fresh unvisited jobs across target portals.")
    
    # Export to data/discovered_jobs.json
    out_file = ROOT_DIR / "data" / "discovered_jobs.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_fresh_jobs, f, indent=2)
    print(f"[SAVED] Exported batch to: {out_file}")

    return all_fresh_jobs

def main():
    parser = argparse.ArgumentParser(description="Multi-Portal Firecrawl Job Hunter (ATS + Gulf Portals)")
    parser.add_argument("--query", default="", help="Custom search query")
    parser.add_argument("--source", choices=["ats", "gulf", "all"], default="all", help="Portal source group")
    parser.add_argument("--limit", type=int, default=10, help="Max results to fetch per query")
    args = parser.parse_args()

    jobs = discover_jobs(query=args.query or None, source=args.source, limit=args.limit)
    for idx, j in enumerate(jobs, 1):
        email_str = f" [Contact: {j['contact_email']}]" if j.get("contact_email") else ""
        print(f"[{idx}] {j['title']} | {j['company']} | {j['url'][:55]}...{email_str}")

if __name__ == "__main__":
    main()
