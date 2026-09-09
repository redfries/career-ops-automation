#!/usr/bin/env python3
"""
sync_to_notion.py
Resilient Notion synchronization engine:
- Authoritative source: data/applications.db (SQLite)
- Idempotent: tracks Notion Page IDs in SQLite sync_log to update in-place without duplicating
- Rate-limited: complies with Notion's 3 req/sec limit
- Exponential backoff: handles 429 and 5xx errors gracefully
- Zero external dependencies: standard library urllib, json, time, sqlite3
"""

import os
import sys
import re
import time
import json
import sqlite3
import argparse
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

NOTION_VERSION = "2022-06-28"

def load_env(env_path: Path) -> Dict[str, str]:
    """Parses .env file into a dictionary."""
    env = {}
    if not env_path.exists():
        return env
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip("\"'")
    return env

def get_notion_headers(api_key: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

def make_request_with_backoff(
    url: str,
    headers: Dict[str, str],
    data: Optional[bytes] = None,
    method: str = "GET",
    max_retries: int = 3
) -> Dict[str, Any]:
    """Makes HTTP request with exponential backoff on 429 or 5xx errors."""
    for attempt in range(max_retries + 1):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="ignore")
            if e.code in (429, 500, 502, 503, 504) and attempt < max_retries:
                wait_time = (2 ** attempt) + 0.5
                print(f"[Notion RateLimit/Server {e.code}] Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
                continue
            raise RuntimeError(f"HTTP {e.code}: {error_body}")
        except Exception as e:
            if attempt < max_retries:
                wait_time = (2 ** attempt) + 0.5
                time.sleep(wait_time)
                continue
            raise

def search_notion_databases(api_key: str) -> List[Dict[str, Any]]:
    url = "https://api.notion.com/v1/search"
    payload = json.dumps({"filter": {"value": "database", "property": "object"}}).encode("utf-8")
    try:
        data = make_request_with_backoff(url, get_notion_headers(api_key), data=payload, method="POST")
        return data.get("results", [])
    except Exception as e:
        print(f"[Warning] Unable to search databases: {e}")
        return []

def get_database_schema(api_key: str, database_id: str) -> Dict[str, Any]:
    url = f"https://api.notion.com/v1/databases/{database_id}"
    try:
        data = make_request_with_backoff(url, get_notion_headers(api_key), method="GET")
        return data.get("properties", {})
    except Exception as e:
        print(f"[Warning] Unable to fetch database schema: {e}")
        return {}

def query_database_pages(api_key: str, database_id: str) -> List[Dict[str, Any]]:
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    try:
        data = make_request_with_backoff(url, get_notion_headers(api_key), data=b"{}", method="POST")
        return data.get("results", [])
    except Exception as e:
        print(f"[Warning] Unable to query database pages: {e}")
        return []

def get_remote_page_id_from_sqlite(conn: sqlite3.Connection, app_id: str) -> Optional[str]:
    cur = conn.cursor()
    cur.execute("SELECT remote_page_id FROM sync_log WHERE application_id = ? AND sync_status = 'SUCCESS' ORDER BY id DESC LIMIT 1", (app_id,))
    row = cur.fetchone()
    return row[0] if row else None

def record_sync_result(
    conn: sqlite3.Connection,
    app_id: str,
    status: str,
    remote_page_id: Optional[str] = None,
    error_msg: Optional[str] = None
):
    with conn:
        conn.execute("""
        INSERT INTO sync_log (application_id, target, remote_page_id, sync_status, error_message, synced_at)
        VALUES (?, 'notion', ?, ?, ?, ?)
        """, (app_id, remote_page_id, status, error_msg, datetime.now().isoformat()))

def build_notion_properties(app: Dict[str, Any], db_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Dynamically maps SQLite application row to Notion properties based on target DB schema."""
    props = {}

    # Find the title property
    title_key = "Company"
    for p_name, p_def in db_schema.items():
        if p_def.get("type") == "title":
            title_key = p_name
            break

    props[title_key] = {"title": [{"text": {"content": app["company"]}}]}

    for p_name, p_def in db_schema.items():
        if p_name == title_key:
            continue
        p_type = p_def.get("type")
        lower_name = p_name.lower()

        if ("role" in lower_name or "position" in lower_name or "title" in lower_name) and app.get("role"):
            if p_type == "rich_text":
                props[p_name] = {"rich_text": [{"text": {"content": app["role"]}}]}

        elif "location" in lower_name and app.get("location"):
            if p_type == "rich_text":
                props[p_name] = {"rich_text": [{"text": {"content": app["location"]}}]}
            elif p_type == "select":
                props[p_name] = {"select": {"name": app["location"][:100]}}

        elif "platform" in lower_name and app.get("platform"):
            if p_type == "select":
                props[p_name] = {"select": {"name": app["platform"][:100]}}
            elif p_type == "rich_text":
                props[p_name] = {"rich_text": [{"text": {"content": app["platform"]}}]}

        elif "status" in lower_name and app.get("status"):
            if p_type in ("select", "status"):
                props[p_name] = {p_type: {"name": app["status"]}}

        elif ("score" in lower_name or "fit" in lower_name) and app.get("holistic_score") is not None:
            if p_type == "number":
                props[p_name] = {"number": round(float(app["holistic_score"]), 2)}
            elif p_type == "rich_text":
                props[p_name] = {"rich_text": [{"text": {"content": f"{app['holistic_score']:.1f} / 5.0"}}]}

        elif ("url" in lower_name or "link" in lower_name) and app.get("source_url"):
            if p_type == "url":
                props[p_name] = {"url": app["source_url"]}

        elif "date" in lower_name and app.get("created_at"):
            date_part = app["created_at"][:10]
            if p_type == "date" and re.match(r"^\d{4}-\d{2}-\d{2}$", date_part):
                props[p_name] = {"date": {"start": date_part}}

        elif "notes" in lower_name and app.get("notes"):
            if p_type == "rich_text":
                props[p_name] = {"rich_text": [{"text": {"content": app["notes"][:2000]}}]}

        elif "id" in lower_name and app.get("id"):
            if p_type == "rich_text":
                props[p_name] = {"rich_text": [{"text": {"content": app["id"]}}]}

    return props

def sync_applications_to_notion(
    api_key: str,
    database_id: str,
    dry_run: bool = False,
    root_dir: Optional[Path] = None
) -> Dict[str, Any]:
    if not root_dir:
        root_dir = Path(__file__).resolve().parent.parent

    db_path = root_dir / "data" / "applications.db"
    if not db_path.exists():
        return {"success": False, "error": f"SQLite database not found at {db_path}"}

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM applications ORDER BY created_at ASC")
    apps = [dict(r) for r in cur.fetchall()]

    print(f"Loaded {len(apps)} applications from SQLite store.")

    if dry_run:
        print("[Dry Run] Skipping remote Notion API mutations.")
        conn.close()
        return {"success": True, "synced_count": len(apps), "dry_run": True}

    headers = get_notion_headers(api_key)
    db_schema = get_database_schema(api_key, database_id)
    existing_pages = query_database_pages(api_key, database_id)

    # Build map of existing pages by Title (Company)
    page_by_company = {}
    for p in existing_pages:
        for p_val in p.get("properties", {}).values():
            if p_val.get("type") == "title":
                title = "".join(t.get("plain_text", "") for t in p_val.get("title", [])).strip().lower()
                if title:
                    page_by_company[title] = p["id"]
                break

    synced_count = 0
    failed_count = 0

    for app in apps:
        app_id = app["id"]
        company = app["company"].strip().lower()
        remote_page_id = get_remote_page_id_from_sqlite(conn, app_id) or page_by_company.get(company)

        properties = build_notion_properties(app, db_schema)

        try:
            if remote_page_id:
                # Update existing page
                url = f"https://api.notion.com/v1/pages/{remote_page_id}"
                payload = json.dumps({"properties": properties}).encode("utf-8")
                make_request_with_backoff(url, headers, data=payload, method="PATCH")
                record_sync_result(conn, app_id, "SUCCESS", remote_page_id=remote_page_id)
                print(f"[Updated Notion] {app['company']} - {app['role']}")
            else:
                # Create new page
                url = "https://api.notion.com/v1/pages"
                payload = json.dumps({
                    "parent": {"database_id": database_id},
                    "properties": properties
                }).encode("utf-8")
                resp = make_request_with_backoff(url, headers, data=payload, method="POST")
                new_page_id = resp.get("id")
                record_sync_result(conn, app_id, "SUCCESS", remote_page_id=new_page_id)
                print(f"[Created Notion] {app['company']} - {app['role']}")

            synced_count += 1
            # Rate limiting delay: 0.35s ~ 2.8 req/sec
            time.sleep(0.35)

        except Exception as e:
            failed_count += 1
            record_sync_result(conn, app_id, "FAILED", error_msg=str(e))
            print(f"[Sync Failed] {app['company']}: {e}")

    conn.close()
    return {
        "success": failed_count == 0,
        "synced_count": synced_count,
        "failed_count": failed_count
    }

def main():
    parser = argparse.ArgumentParser(description="Synchronize SQLite applications to Notion.")
    parser.add_argument("--dry-run", action="store_true", help="Inspect and validate without sending requests")
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parent.parent
    env = load_env(root_dir / ".env")
    api_key = env.get("NOTION_API_KEY")
    database_id = env.get("NOTION_DATABASE_ID")

    if not api_key:
        print("[Error] NOTION_API_KEY not found in .env.")
        sys.exit(1)

    if args.dry_run:
        print("[Dry Run Mode Enabled]")
        res = sync_applications_to_notion(api_key or "dry_run_key", "dummy_db_id", dry_run=True, root_dir=root_dir)
        print(f"\nDry Run Complete: {res.get('synced_count', 0)} applications validated from SQLite.")
        return

    print("Checking Notion API access...")
    dbs = search_notion_databases(api_key)
    print(f"Accessible databases: {len(dbs)}")

    if not database_id:
        if len(dbs) == 1:
            database_id = dbs[0]["id"]
            print(f"Using database: {database_id}")
        else:
            print("[Error] Please configure NOTION_DATABASE_ID in .env or share your database with the integration.")
            sys.exit(1)

    res = sync_applications_to_notion(api_key, database_id, dry_run=False, root_dir=root_dir)
    print(f"\nSync complete. Synced: {res.get('synced_count', 0)}, Failed: {res.get('failed_count', 0)}")

if __name__ == "__main__":
    main()
