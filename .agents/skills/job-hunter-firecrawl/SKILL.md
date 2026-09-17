---
name: job-hunter-firecrawl
description: Automates discovering, scraping, evaluating (Career-Ops A-H), and tracking AI / ML jobs across Saudi Arabia, UAE, and Remote portals. Runs deterministic 8-stage pipeline with Tsenta ATS resume engine (balanced mode, strictly 2-page, zero-Iqama), Firecrawl decision-maker intelligence, automated Resend email outreach, and candidate portal cockpit.
---

# Career-Ops Deterministic Automation Pipeline

This skill governs the end-to-end execution of the **Deterministic 8-Stage Career-Ops Pipeline** ([`scripts/pipeline_orchestrator.py`](scripts/pipeline_orchestrator.py)) powered by the **Tsenta-Inspired ATS Resume Tailoring Engine** ([`scripts/tsenta_ats_engine.py`](scripts/tsenta_ats_engine.py)), Firecrawl Contact Intelligence, and Resend Recruiter Outreach.

---

## 1. Core Operating Principles & Strict Invariants

1. **Strict Provenance & Anti-Hallucination**:
   - All candidate facts derive strictly from [`data/canonical_profile.json`](data/canonical_profile.json).
   - Commercial experience: 22 months QA Automation Engineer at TCS (Salesforce, Tosca, Selenium, Python, API testing, SQL validation, qTest).
   - Academic employment: Graduate Assistant at KFUPM (Oct 2024 – Apr 2026).
   - Research & Master's AI Projects: KFUPM & BRAIN Lab (*Personalized Reading Experience*, *Arabic Cheque OCR*, *ReSeeAI*).
   - **NEVER** claim commercial AI engineering employment at TCS.
   - **NEVER** cite quarantined template samples (DEFCON, CODEGATE, POSTECH).

2. **Strict Resume Zero-Iqama Invariant**:
   - **NEVER put "Transferable Iqama" or "Iqama" in the resume text.**
   - The resume PDF is a global technical document and must strictly state location: `Based in Dhahran, Saudi Arabia.`
   - Validated programmatically with zero tolerance on every compilation.

3. **Strict 2-Page Resume Geometry**:
   - Every resume compiled with Tectonic is programmatically asserted to have `page_count == 2` via PyMuPDF.
   - Page 1: Header + About Me + Skills Matrix + Top 3 Projects.
   - Page 2: Work Experience (11 detailed bullets) + Education (KFUPM MS in AI, JNTUA B.Tech) + Extracurricular (Solution Hackathon + Quantum Computing Symposium).

4. **Human-in-the-Loop Portal Submission (NO Autonomous Browser Automation)**:
   - **NEVER** attempt autonomous Playwright browser clicks on LinkedIn, Workable, or company portals.
   - Portal submission is performed directly by the candidate.
   - The pipeline finishes with authoritative proof and outputs the direct link for candidate submission.
   - Once submitted, record status via:
     ```powershell
     python scripts/pipeline_orchestrator.py --confirm-applied <JOB_ID> --notes "Applied on portal"
     ```

---

## 2. Multi-Portal Ingestion (Firecrawl)

### Method A: Automated ATS & Gulf Portals Discovery
* **Command**:
  ```powershell
  # Gulf portals (sa.indeed.com, ae.indeed.com, bayt.com, naukrigulf.com):
  python scripts/firecrawl_job_hunter.py --source gulf --limit 10

  # Global ATS (Greenhouse, Lever, Ashby):
  python scripts/firecrawl_job_hunter.py --source ats --limit 10

  # All portals:
  python scripts/firecrawl_job_hunter.py --source all --limit 10
  ```
* Automatically extracts direct hiring/recruiter email addresses from postings when available.

---

## 3. Evaluation & Batch Digest (Chat Cockpit)

* **Command**:
  ```powershell
  python -u scripts/run_batch.py --evaluate
  ```
* Evaluates discovered listings against canonical profile across:
  - **Dimension 1: Eligibility Gate** (Work rights: KSA Transferable Iqama, Global Remote B2B, India citizen; experience $\le 4$ years).
  - **Dimension 2: Capability Match** (Computer Vision, ViT, RAG, QA automation).
  - **Dimension 3: Preference Match** (Saudi Arabia > UAE > Remote).
* Formats concise batch cards in chat with match scores (0–100%) and archetype tags.

---

## 4. Deterministic 8-Stage Pipeline & Tsenta ATS Tailoring

Run the full end-to-end pipeline for any shortlisted job:
```powershell
# Run specific job ID (default mode: balanced):
python scripts/pipeline_orchestrator.py --job-id <JOB_ID> --mode balanced

# Process next highest-scoring shortlisted opportunity:
python scripts/pipeline_orchestrator.py --next-shortlisted --mode balanced

# Re-run tailoring without resending email:
python scripts/pipeline_orchestrator.py --job-id <JOB_ID> --mode balanced --skip-email
```

### The 8 Deterministic Stages:
1. **Stage 1/8: Ingestion & Validation & Direct Link Resolution**
   - Ingests from `data/jobs.db`, verifies company/title/description, creates `applications/<date>_<company>_<job_id>/`.
2. **Stage 2/8: Technical Taxonomy & Keyword Extraction**
   - Decomposes JD into Must-Haves, Nice-to-Haves, Disqualifiers, and Technical Taxonomy.
3. **Stage 3/8: Tsenta 5-Stage ATS Resume Tailoring & Compilation**
   - Applies **`balanced`** mode: active action verbs, dynamic project re-ranking, front-loaded skills, TCS QA + KFUPM GA bullet reframing, zero Iqama references.
   - Compiles via Tectonic and programmatically asserts strict 2-page invariant.
4. **Stage 4/8: Resume vs. JD Alignment & Provenance Audit**
   - Computes ATS match score lift (e.g. +30.5%) and writes `alignment_audit.json` and `alignment_audit.md`.
5. **Stage 5/8: Firecrawl Contact Intelligence Engine**
   - Identifies key decision makers (Engineering Managers, Tech Recruiters) and recommended company email patterns.
6. **Stage 6/8: Recruiter Pitch & Application Package Assembly**
   - Assembles tailored pitch and `application_package.json`.
7. **Stage 7/8: Automated Resend Recruiter Outreach Engine**
   - Dispatches natural executive outreach email with attached tailored PDF resume via Resend API.
   - Saves delivery proof to `email_sent_receipt.json` and records Resend message ID into SQLite notes.
8. **Stage 8/8: Candidate Review Cockpit & DB State Invariant**
   - Locks DB status as `tailored` (or preserves `applied`).
   - Displays authoritative Resend proof and outputs direct portal link for candidate submission.

---

## 5. Portal Submission & Tracking

* **Portal Application**: Performed directly by candidate using the verified direct link.
* **Recording Confirmation**:
  ```powershell
  python scripts/pipeline_orchestrator.py --confirm-applied <JOB_ID> --notes "Applied on LinkedIn portal"
  ```
* **SQLite Database**: `data/jobs.db`
* **Sync & Export**:
  ```powershell
  python scripts/sync_to_notion.py
  ```
