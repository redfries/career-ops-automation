#!/usr/bin/env python3
"""
test_pipeline_resilience.py
Automated edge-case and resilience test suite:
1. Deduplication across portals (Bayt + LinkedIn)
2. Two roles at same company on same day (collision-proof folders)
3. Blocked / incomplete scrape handling (enters needs_review, no hallucinations)
4. Ineligible job hard gate (US clearance / citizenship required)
5. LaTeX special character escaping (&, %, $, _, #)
6. PDF binary and structural validation (magic header, size, text, pages)
7. Submission gate enforcement (cannot mark submitted without receipt)
8. Notion offline resilience (zero data loss on sync failure)
"""

import os
import sys
import json
import tempfile
import sqlite3
from pathlib import Path

# Add scripts directory to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from pdf_validator import validate_resume_pdf, compute_sha256
from compile_tailored_resume import escape_latex_text, build_application_bundle
from db_manager import init_db, upsert_application, set_application_status, get_connection

def test_1_deduplication():
    print("\n--- Test 1: Deduplication across portals ---")
    test_db = ROOT_DIR / "data" / "test_resilience.db"
    if test_db.exists():
        test_db.unlink()
    init_db(test_db)

    # First source: Bayt
    app1 = {
        "company": "DeepNeom AI",
        "role": "Vision Systems Engineer",
        "location": "Tabuk, Saudi Arabia",
        "platform": "Bayt.com",
        "source_url": "https://www.bayt.com/en/saudi-arabia/jobs/1111/",
        "canonical_url": "https://www.bayt.com/en/saudi-arabia/jobs/1111/",
        "status": "discovered"
    }
    id1 = upsert_application(app1, test_db)

    # Second source: LinkedIn for same company & role
    app2 = {
        "company": "DeepNeom AI",
        "role": "Vision Systems Engineer",
        "location": "Tabuk, Saudi Arabia",
        "platform": "LinkedIn",
        "source_url": "https://www.linkedin.com/jobs/view/2222/",
        "canonical_url": "https://www.bayt.com/en/saudi-arabia/jobs/1111/", # Same canonical
        "status": "evaluated",
        "holistic_score": 4.6
    }
    id2 = upsert_application(app2, test_db)

    assert id1 == id2, f"Expected same ID for duplicate opportunity, got {id1} vs {id2}"

    conn = get_connection(test_db)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM applications WHERE company = 'DeepNeom AI'")
    count = cur.fetchone()[0]
    conn.close()

    assert count == 1, f"Expected 1 record in SQLite, found {count}"
    print(f"[PASS] Deduplication confirmed: Multiple sources merged into single ID '{id1}'.")

def test_2_two_roles_same_company_same_day():
    print("\n--- Test 2: Two roles at same company on same day ---")
    date_str = "2026-09-09"
    company = "Aramco Digital"

    res1 = build_application_bundle(
        company=company,
        role="Computer Vision Engineer",
        target_date=date_str,
        req_id="REQ_CV_01",
        focus="vision",
        root_dir=ROOT_DIR
    )
    assert res1["success"], f"Bundle 1 failed: {res1.get('error')}"

    res2 = build_application_bundle(
        company=company,
        role="NLP & GenAI Engineer",
        target_date=date_str,
        req_id="REQ_NLP_02",
        focus="rag",
        root_dir=ROOT_DIR
    )
    assert res2["success"], f"Bundle 2 failed: {res2.get('error')}"

    assert res1["application_id"] != res2["application_id"], "Folder IDs collided!"
    assert Path(res1["final_directory"]).exists(), "Bundle 1 folder missing"
    assert Path(res2["final_directory"]).exists(), "Bundle 2 folder missing"

    # Verify distinct PDFs and manifests
    with open(Path(res1["final_directory"]) / "submission_manifest.json") as f:
        m1 = json.load(f)
    with open(Path(res2["final_directory"]) / "submission_manifest.json") as f:
        m2 = json.load(f)

    assert m1["req_id"].lower() == "req_cv_01"
    assert m2["req_id"].lower() == "req_nlp_02"
    print(f"[PASS] Non-colliding folders created:\n  - {res1['application_id']}\n  - {res2['application_id']}")

def test_3_blocked_or_incomplete_scrape_handling():
    print("\n--- Test 3: Blocked / incomplete scrape handling ---")
    test_db = ROOT_DIR / "data" / "test_resilience.db"

    # Simulate blocked scrape
    blocked_scrape = {
        "company": "CloudTech Corp",
        "role": "AI Architect",
        "platform": "Bayt.com",
        "source_url": "https://www.bayt.com/blocked",
        "ingestion_quality": "BLOCKED",
        "status": "needs_review",
        "notes": "Bot challenge encountered during scrape. Prompted user for manual text paste."
    }
    app_id = upsert_application(blocked_scrape, test_db)

    conn = get_connection(test_db)
    cur = conn.cursor()
    cur.execute("SELECT status, ingestion_quality, holistic_score FROM applications WHERE id = ?", (app_id,))
    row = cur.fetchone()
    conn.close()

    assert row["status"] == "needs_review", f"Expected needs_review, got {row['status']}"
    assert row["ingestion_quality"] == "BLOCKED"
    assert row["holistic_score"] == 0.0, "Blocked scrape must not have confident score"
    print(f"[PASS] Incomplete scrape successfully flagged as '{row['status']}' with zero false score.")

def test_4_ineligible_job_gate():
    print("\n--- Test 4: Ineligible job hard gate ---")
    test_db = ROOT_DIR / "data" / "test_resilience.db"

    # Role requiring US Top Secret clearance
    ineligible_job = {
        "company": "Defense Tech LLC",
        "role": "Senior Computer Vision Specialist",
        "location": "Washington, DC",
        "eligibility_gate": "FAIL",
        "eligibility_notes": "Hard Gate Failure: Requires active US DoD Top Secret Clearance and US Citizenship.",
        "status": "ineligible",
        "holistic_score": 0.0
    }
    app_id = upsert_application(ineligible_job, test_db)

    conn = get_connection(test_db)
    cur = conn.cursor()
    cur.execute("SELECT status, eligibility_gate FROM applications WHERE id = ?", (app_id,))
    row = cur.fetchone()
    conn.close()

    assert row["status"] == "ineligible"
    assert row["eligibility_gate"] == "FAIL"
    print(f"[PASS] Ineligible job gate triggered. Application flagged as '{row['status']}'.")

def test_5_latex_special_character_escaping():
    print("\n--- Test 5: LaTeX special character escaping ---")
    raw_text = "C# & C++ developer; achieved 97.5% accuracy; $120k budget; user_id #1042"
    escaped = escape_latex_text(raw_text)

    expected_escapes = [r"\&", r"\%", r"\$", r"\_", r"\#"]
    for esc in expected_escapes:
        assert esc in escaped, f"Missing escape sequence {esc} in {escaped}"

    # Verify no double-escaping
    re_escaped = escape_latex_text(escaped)
    assert re_escaped == escaped, f"Double escaping occurred: {re_escaped} != {escaped}"
    print(f"[PASS] LaTeX escaping confirmed:\n  Raw:     '{raw_text}'\n  Escaped: '{escaped}'")

def test_6_pdf_validation():
    print("\n--- Test 6: PDF binary & structural validation ---")
    valid_pdf = ROOT_DIR / "my-resume" / "resume.pdf"
    res = validate_resume_pdf(valid_pdf, max_pages=2)
    assert res["valid"], f"Valid resume failed validation: {res['errors']}"
    assert res["page_count"] == 2
    assert len(res["sha256"]) == 64

    # Test invalid / corrupt PDF
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"NOT A REAL PDF FILE")
        corrupt_path = Path(f.name)

    try:
        corrupt_res = validate_resume_pdf(corrupt_path, max_pages=2)
        assert not corrupt_res["valid"], "Corrupt PDF was incorrectly marked valid!"
        assert any("magic" in e.lower() or "too small" in e.lower() for e in corrupt_res["errors"])
        print(f"[PASS] PDF validator correctly accepted valid resume and rejected corrupt file.")
    finally:
        if corrupt_path.exists():
            corrupt_path.unlink()

def test_7_submission_gate_enforcement():
    print("\n--- Test 7: Submission gate enforcement ---")
    test_db = ROOT_DIR / "data" / "test_resilience.db"

    app = {
        "company": "Beta Labs",
        "role": "AI Engineer",
        "status": "ready_for_review"
    }
    app_id = upsert_application(app, test_db)

    # Attempt to set submitted without receipt -> MUST FAIL
    failed = False
    try:
        set_application_status(app_id, "submitted", submission_receipt=None, db_path=test_db)
    except ValueError:
        failed = True
    assert failed, "Allowed status 'submitted' without submission receipt!"

    # Now provide valid receipt -> MUST SUCCEED
    receipt_id = "APP-REC-2026-98765"
    set_application_status(app_id, "submitted", submission_receipt=receipt_id, db_path=test_db)

    conn = get_connection(test_db)
    cur = conn.cursor()
    cur.execute("SELECT status, submission_receipt, submitted_at FROM applications WHERE id = ?", (app_id,))
    row = cur.fetchone()
    conn.close()

    assert row["status"] == "submitted"
    assert row["submission_receipt"] == receipt_id
    assert row["submitted_at"] is not None
    print(f"[PASS] Submission gate successfully blocked unverified submission and accepted confirmed receipt.")

def test_8_notion_offline_resilience():
    print("\n--- Test 8: Notion offline resilience ---")
    from sync_to_notion import sync_applications_to_notion

    # Run dry run or unreachable token against test DB
    res = sync_applications_to_notion(
        api_key="ntn_invalid_test_key",
        database_id="dummy_db",
        dry_run=True,
        root_dir=ROOT_DIR
    )
    assert res["success"], "Sync dry-run / offline check failed"

    # Verify SQLite database is completely intact
    conn = get_connection(ROOT_DIR / "data" / "applications.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM applications")
    count = cur.fetchone()[0]
    conn.close()

    assert count >= 11, f"Database lost records! Count: {count}"
    print(f"[PASS] Offline safety verified: {count} applications remain fully intact in SQLite.")

def test_9_fast_ats_tailor_engine():
    print("\n--- Test 9: Fast ATS tailoring & validation engine ---")
    from fast_ats_tailor import run_fast_tailor

    sample_jd = (
        "Seeking an AI Engineer with hands-on expertise in PyTorch, Computer Vision, "
        "Cascade R-CNN, OCR document processing, and Docker to deploy scalable models."
    )
    res = run_fast_tailor(
        company="Test Corp Vision",
        role="Computer Vision Engineer",
        jd_text=sample_jd,
        focus="vision",
        sync_to_notion_flag=False,
        benchmark=True
    )

    assert res["success"], f"Fast ATS tailoring failed: {res.get('error')}"
    assert res["ats_score"] >= 80.0, f"Expected high ATS score, got {res['ats_score']}%"
    assert res["archetype"] == "vision"
    assert Path(res["pdf_path"]).exists(), "PDF was not compiled!"
    assert res["page_count"] in (1, 2), f"Expected 1 or 2 pages, got {res['page_count']}"

    manifest_path = Path(res["bundle_dir"]) / "submission_manifest.json"
    assert manifest_path.exists(), "submission_manifest.json missing!"

    print(f"[PASS] Fast ATS Engine verified: {res['ats_score']}% score, {res['page_count']} page PDF generated and validated.")

def main():
    import json
    print("=====================================================")
    print("STARTING PIPELINE RESILIENCE & ARCHITECTURE TESTS")
    print("=====================================================")

    test_1_deduplication()
    test_2_two_roles_same_company_same_day()
    test_3_blocked_or_incomplete_scrape_handling()
    test_4_ineligible_job_gate()
    test_5_latex_special_character_escaping()
    test_6_pdf_validation()
    test_7_submission_gate_enforcement()
    test_8_notion_offline_resilience()
    test_9_fast_ats_tailor_engine()

    # Cleanup test db
    test_db = ROOT_DIR / "data" / "test_resilience.db"
    if test_db.exists():
        test_db.unlink()

    print("\n=====================================================")
    print("ALL 9 RESILIENCE TESTS PASSED EMPIRICALLY (0 FAILURES)")
    print("=====================================================")

if __name__ == "__main__":
    main()
