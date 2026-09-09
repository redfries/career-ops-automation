#!/usr/bin/env python3
"""
db_manager.py
Authoritative SQLite storage manager for job applications:
- Enforces normalized schema and strict lifecycle states
- Prevents duplicate applications across portals
- Enforces submission evidence gates
- Generates human-readable Markdown tracker views
"""

import os
import sys
import re
import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

VALID_STATUSES = [
    "discovered",
    "ingestion_uncertain",
    "needs_review",
    "ineligible",
    "evaluated",
    "prepared",
    "ready_for_review",
    "approved",
    "submitted",
    "submission_uncertain",
    "closed",
    "rejected"
]

def get_db_path(root_dir: Optional[Path] = None) -> Path:
    if not root_dir:
        root_dir = Path(__file__).resolve().parent.parent
    data_dir = root_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "applications.db"

def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(db_path: Optional[Path] = None):
    """Creates database schema if not exists."""
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS applications (
            id TEXT PRIMARY KEY,
            req_id TEXT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            location TEXT,
            platform TEXT,
            source_url TEXT,
            canonical_url TEXT,
            status TEXT NOT NULL DEFAULT 'discovered',
            eligibility_gate TEXT DEFAULT 'PASS',
            eligibility_notes TEXT,
            capability_score REAL DEFAULT 0.0,
            preference_score REAL DEFAULT 0.0,
            holistic_score REAL DEFAULT 0.0,
            ingestion_quality TEXT DEFAULT 'HIGH',
            folder_path TEXT,
            pdf_sha256 TEXT,
            submission_receipt TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            submitted_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_apps_company_role ON applications (company, role);
        CREATE INDEX IF NOT EXISTS idx_apps_status ON applications (status);
        CREATE INDEX IF NOT EXISTS idx_apps_canonical_url ON applications (canonical_url);

        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
            block_a_overview TEXT,
            block_b_requirements TEXT,
            block_c_hard_gates TEXT,
            block_d_evidence TEXT,
            block_e_culture TEXT,
            block_f_comp TEXT,
            block_g_legitimacy TEXT,
            block_h_screener TEXT,
            evaluated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS screener_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
            question_text TEXT NOT NULL,
            answer_text TEXT NOT NULL,
            verified_source TEXT
        );

        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
            target TEXT NOT NULL DEFAULT 'notion',
            remote_page_id TEXT,
            sync_status TEXT NOT NULL,
            error_message TEXT,
            synced_at TEXT NOT NULL
        );
        """)
    conn.close()

def upsert_application(app_data: Dict[str, Any], db_path: Optional[Path] = None) -> str:
    """Inserts or updates an application record atomically."""
    conn = get_connection(db_path)
    now = datetime.now().isoformat()
    app_id = app_data.get("id")

    # If ID not provided, check if company + role already exists
    if not app_id:
        company = app_data.get("company", "").strip()
        role = app_data.get("role", "").strip()
        cur = conn.cursor()
        cur.execute("SELECT id FROM applications WHERE LOWER(company) = LOWER(?) AND LOWER(role) = LOWER(?)", (company, role))
        row = cur.fetchone()
        if row:
            app_id = row["id"]
        else:
            # Generate deterministic slug ID
            comp_slug = re.sub(r"[^\w-]", "", company.lower().replace(" ", "-"))
            role_slug = re.sub(r"[^\w-]", "", role.lower().replace(" ", "-"))
            app_id = f"{datetime.now().strftime('%Y-%m-%d')}_{comp_slug}_{role_slug}"
            app_data["id"] = app_id

    # Validate status
    status = app_data.get("status", "discovered")
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {VALID_STATUSES}")

    # Enforce submission gate
    if status == "submitted" and not app_data.get("submission_receipt"):
        raise ValueError("Cannot mark application 'submitted' without verified 'submission_receipt'. Use 'prepared' or 'ready_for_review'.")

    with conn:
        conn.execute("""
        INSERT INTO applications (
            id, req_id, company, role, location, platform, source_url, canonical_url,
            status, eligibility_gate, eligibility_notes, capability_score, preference_score,
            holistic_score, ingestion_quality, folder_path, pdf_sha256, submission_receipt,
            notes, created_at, updated_at, submitted_at
        ) VALUES (
            :id, :req_id, :company, :role, :location, :platform, :source_url, :canonical_url,
            :status, :eligibility_gate, :eligibility_notes, :capability_score, :preference_score,
            :holistic_score, :ingestion_quality, :folder_path, :pdf_sha256, :submission_receipt,
            :notes, :created_at, :updated_at, :submitted_at
        )
        ON CONFLICT(id) DO UPDATE SET
            req_id = COALESCE(excluded.req_id, applications.req_id),
            company = excluded.company,
            role = excluded.role,
            location = COALESCE(excluded.location, applications.location),
            platform = COALESCE(excluded.platform, applications.platform),
            source_url = COALESCE(excluded.source_url, applications.source_url),
            canonical_url = COALESCE(excluded.canonical_url, applications.canonical_url),
            status = excluded.status,
            eligibility_gate = COALESCE(excluded.eligibility_gate, applications.eligibility_gate),
            eligibility_notes = COALESCE(excluded.eligibility_notes, applications.eligibility_notes),
            capability_score = COALESCE(excluded.capability_score, applications.capability_score),
            preference_score = COALESCE(excluded.preference_score, applications.preference_score),
            holistic_score = COALESCE(excluded.holistic_score, applications.holistic_score),
            ingestion_quality = COALESCE(excluded.ingestion_quality, applications.ingestion_quality),
            folder_path = COALESCE(excluded.folder_path, applications.folder_path),
            pdf_sha256 = COALESCE(excluded.pdf_sha256, applications.pdf_sha256),
            submission_receipt = COALESCE(excluded.submission_receipt, applications.submission_receipt),
            notes = COALESCE(excluded.notes, applications.notes),
            updated_at = excluded.updated_at,
            submitted_at = COALESCE(excluded.submitted_at, applications.submitted_at)
        """, {
            "id": app_id,
            "req_id": app_data.get("req_id"),
            "company": app_data.get("company", "Unknown"),
            "role": app_data.get("role", "Unknown"),
            "location": app_data.get("location"),
            "platform": app_data.get("platform"),
            "source_url": app_data.get("source_url"),
            "canonical_url": app_data.get("canonical_url"),
            "status": status,
            "eligibility_gate": app_data.get("eligibility_gate", "PASS"),
            "eligibility_notes": app_data.get("eligibility_notes"),
            "capability_score": app_data.get("capability_score", 0.0),
            "preference_score": app_data.get("preference_score", 0.0),
            "holistic_score": app_data.get("holistic_score", 0.0),
            "ingestion_quality": app_data.get("ingestion_quality", "HIGH"),
            "folder_path": app_data.get("folder_path"),
            "pdf_sha256": app_data.get("pdf_sha256"),
            "submission_receipt": app_data.get("submission_receipt"),
            "notes": app_data.get("notes"),
            "created_at": app_data.get("created_at", now),
            "updated_at": now,
            "submitted_at": app_data.get("submitted_at")
        })

    conn.close()
    return app_id

def set_application_status(
    app_id: str,
    new_status: str,
    submission_receipt: Optional[str] = None,
    db_path: Optional[Path] = None
) -> bool:
    """Updates lifecycle status with submission verification."""
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{new_status}'. Allowed: {VALID_STATUSES}")

    if new_status == "submitted" and not submission_receipt:
        raise ValueError("Cannot set status to 'submitted' without verified 'submission_receipt'.")

    conn = get_connection(db_path)
    now = datetime.now().isoformat()
    submitted_at = now if new_status == "submitted" else None

    with conn:
        conn.execute("""
        UPDATE applications
        SET status = ?,
            submission_receipt = COALESCE(?, submission_receipt),
            submitted_at = COALESCE(?, submitted_at),
            updated_at = ?
        WHERE id = ?
        """, (new_status, submission_receipt, submitted_at, now, app_id))
    conn.close()
    return True

def export_markdown_tracker(output_path: Path, db_path: Optional[Path] = None):
    """Regenerates the Markdown tracker table directly from SQLite."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
    SELECT id, company, role, location, platform, source_url, holistic_score,
           status, created_at, notes, folder_path, pdf_sha256
    FROM applications
    ORDER BY created_at DESC
    """)
    rows = cur.fetchall()
    conn.close()

    lines = [
        "# Active Job Application Tracker",
        "",
        "> **Notice**: This file is an auto-generated view from the authoritative SQLite database (`data/applications.db`).",
        "> To modify statuses or records, use `scripts/db_manager.py` or the Career-Ops pipeline.",
        "",
        f"*Last regenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
        "| # | Company | Role | Location | Platform | Source Link | Holistic Fit | Status | Date Added | Notes / Verified Bundle |",
        "| :- | :- | :- | :- | :- | :- | :- | :- | :- | :- |"
    ]

    for idx, r in enumerate(rows, 1):
        link_str = f"[Link]({r['source_url']})" if r["source_url"] else "Direct"
        score_str = f"**{r['holistic_score']:.1f} / 5.0**" if r["holistic_score"] > 0 else "Pending"
        date_str = r["created_at"][:10] if r["created_at"] else ""
        notes_str = r["notes"] or ""
        if r["folder_path"]:
            notes_str += f" [Bundle: `{Path(r['folder_path']).name}`]"

        lines.append(
            f"| {idx} | **{r['company']}** | {r['role']} | {r['location'] or 'Remote'} | "
            f"{r['platform'] or 'Direct'} | {link_str} | {score_str} | `{r['status']}` | {date_str} | {notes_str} |"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

def seed_from_legacy_tracker(tracker_path: Path, db_path: Optional[Path] = None):
    """Parses existing active_application_tracker.md and seeds into SQLite."""
    if not tracker_path.exists():
        return 0

    with open(tracker_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    table_lines = [l.strip() for l in lines if l.strip().startswith("|") and not l.strip().startswith("| #") and not l.strip().startswith("| :-")]
    count = 0
    for line in table_lines:
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) >= 8:
            company = parts[1].replace("**", "").strip()
            role = parts[2].strip()
            location = parts[3].strip()
            platform = parts[4].strip()
            link_raw = parts[5].strip()
            fit_raw = parts[6].replace("**", "").replace("/ 5.0", "").strip()
            status_raw = parts[7].replace("`", "").strip()
            date_added = parts[8].strip() if len(parts) > 8 else datetime.now().strftime("%Y-%m-%d")
            notes = parts[9].strip() if len(parts) > 9 else ""

            # Extract URL
            url_match = re.search(r"\((https?://[^\)]+)\)", link_raw)
            clean_url = url_match.group(1) if url_match else (link_raw if link_raw.startswith("http") else None)

            # Map score
            try:
                holistic = float(fit_raw)
            except ValueError:
                holistic = 0.0

            # Map legacy status to valid enum
            status_map = {
                "Ready to Apply": "ready_for_review",
                "To Apply": "prepared",
                "Applied": "submission_uncertain", # Map legacy unverified 'Applied' to 'submission_uncertain'
                "Screening": "submitted",
                "Rejected": "rejected"
            }
            norm_status = status_map.get(status_raw, "discovered")

            upsert_application({
                "company": company,
                "role": role,
                "location": location,
                "platform": platform,
                "source_url": clean_url,
                "canonical_url": clean_url,
                "status": norm_status,
                "holistic_score": holistic,
                "capability_score": holistic * 20.0,
                "preference_score": 90.0,
                "created_at": date_added,
                "notes": notes
            }, db_path)
            count += 1

    return count

def main():
    parser = argparse.ArgumentParser(description="Authoritative SQLite Database Manager for Job Applications.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    subparsers.add_parser("init", help="Initialize SQLite tables")

    # seed
    subparsers.add_parser("seed", help="Migrate initial entries from active_application_tracker.md")

    # export
    subparsers.add_parser("export", help="Regenerate active_application_tracker.md from SQLite")

    # list
    list_parser = subparsers.add_parser("list", help="List applications")
    list_parser.add_argument("--status", default=None, help="Filter by status")

    # set-status
    status_parser = subparsers.add_parser("set-status", help="Update application lifecycle status")
    status_parser.add_argument("--id", required=True, help="Application ID")
    status_parser.add_argument("--status", required=True, choices=VALID_STATUSES, help="New status")
    status_parser.add_argument("--receipt", default=None, help="Submission confirmation ID / evidence")

    args = parser.parse_args()
    root_dir = Path(__file__).resolve().parent.parent

    if args.command == "init":
        init_db()
        print("SQLite database initialized at data/applications.db")

    elif args.command == "seed":
        init_db()
        tracker_file = root_dir / "job_research" / "active_application_tracker.md"
        count = seed_from_legacy_tracker(tracker_file)
        print(f"Seeded {count} applications into SQLite database.")
        export_markdown_tracker(tracker_file)
        print(f"Regenerated {tracker_file.name}")

    elif args.command == "export":
        tracker_file = root_dir / "job_research" / "active_application_tracker.md"
        export_markdown_tracker(tracker_file)
        print(f"Exported database state to {tracker_file.name}")

    elif args.command == "list":
        conn = get_connection()
        cur = conn.cursor()
        if args.status:
            cur.execute("SELECT id, company, role, status, holistic_score FROM applications WHERE status = ? ORDER BY created_at DESC", (args.status,))
        else:
            cur.execute("SELECT id, company, role, status, holistic_score FROM applications ORDER BY created_at DESC")
        rows = cur.fetchall()
        print(f"\nFound {len(rows)} applications:")
        for r in rows:
            print(f" -> [{r['status']:<18}] {r['company']} - {r['role']} (Fit: {r['holistic_score']:.1f}) [ID: {r['id']}]")
        conn.close()

    elif args.command == "set-status":
        try:
            set_application_status(args.id, args.status, args.receipt)
            print(f"Application {args.id} status updated to '{args.status}'.")
            # Automatically re-export markdown
            tracker_file = root_dir / "job_research" / "active_application_tracker.md"
            export_markdown_tracker(tracker_file)
        except Exception as e:
            print(f"[Error] {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
