# Agent Standard Operating Procedure (SOP) — Career-Ops Automation

> **CRITICAL DIRECTIVE FOR ALL AI AGENTS (Claude Code, Antigravity, Gemini, Codex)**:
> This workspace implements a deterministic, fail-safe automation architecture modeled after production workflow engines (like n8n). Agents operating in this codebase must strictly adhere to these instructions. **Never bypass deterministic scripts with conversational improvisation.**

---

## 1. Core Architectural Principle: Code as Orchestrator, Model as Leaf

```
┌─────────────────────────────────────────────────────────────┐
│                 DETERMINISTIC PYTHON ENGINE                 │
│  (State Machine, Hard Assertions, SQLite State, Timeouts)   │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
       [LLM Worker Node]               [Playwright Node]
    - Keyword Analysis              - DOM Autofill (2 sec)
    - Resume Section Highlighting   - 150ms File Attachment
    - Screener Answer Generation    - 45s Mediator Supervisor
```

1. **Deterministic Control Flow**: Execution transitions (`shortlisted` ➔ `tailored` ➔ `applied`) are managed in code and tracked in `data/jobs.db`. The agent must never "decide" whether a step succeeded; it must execute the deterministic scripts and verify disk state.
2. **Fail-Fast Invariants**: If an exit code is non-zero, immediately halt. Never pretend an operation succeeded. Never substitute mock/fake data.
3. **No 30-Minute Hangs**: Every browser interaction is protected by an overall 90-second execution deadline and a 45-second Mediator supervisor timer. If a portal stalls, the engine logs diagnostic screenshots, updates the database, closes the tab, and cleanly advances.

---

## 2. Non-Negotiable Invariants & Candidate Guardrails

### A. Strict Candidate Provenance (Zero Hallucination)
All candidate information derives exclusively from [`data/canonical_profile.json`](data/canonical_profile.json):
* **Candidate**: Shabaaz Hussain Shaik (Location: Dhahran, Saudi Arabia).
* **AI & Machine Learning Research**:
  * King Fahd University of Petroleum & Minerals (KFUPM) Masters in AI & BRAIN Lab.
  * Projects: *Personalized Reading Experience* (Vision Transformers, Eye Tracking, FastAPI), *Arabic Cheque OCR* (CNN-BiLSTM, CTC loss), *ReSeeAI* (Vision-Language multimodal assistant).
* **Commercial Industry Experience**:
  * Tata Consultancy Services (TCS) — QA Automation Engineer (Nov 2022 – Aug 2024, 22 months).
  * Scope: Salesforce test automation, Python, Selenium, Tosca Vision AI.
  * ⚠️ **NEVER claim commercial AI engineering employment at TCS.**
* **Work Authorization**:
  * Saudi Arabia: Resident with **Transferable Iqama** (No visa sponsorship required).
  * India: Citizen (Full citizen work rights).
  * Global Remote: Eligible for B2B contractor / Deel engagements.
  * United States / EU: Ineligible without employer visa sponsorship (H-1B, Blue Card).

### B. Strict 2-Page Resume Policy
* The candidate's resume **strictly maintains a 2-page format**.
* **NEVER** shrink font, remove margins, or compress sections to force a 1-page layout.
* Section structure in [`my-resume/`](my-resume/) must be preserved:
  1. Header (Contact, LinkedIn, GitHub, Portfolio)
  2. About Me / Skills (*Placed before work experience per user directive*)
  3. Projects (*ViT, Arabic OCR, ReSeeAI*)
  4. Work Experience (*KFUPM Graduate Assistant, TCS Systems Engineer*)
  5. Education (*KFUPM MS in AI, JNTUA B.Tech CSE*)
  6. Extracurricular Activities (*Community Volunteering*)

---

## 3. The 5 Application Lifecycle States

All listings in [`data/jobs.db`](data/jobs.db) exist in one of these authoritative states:

| Status | Meaning | Action Needed |
| :--- | :--- | :--- |
| `shortlisted` | Scored $\ge 80\%$ by evaluation filter | Run `fast_ats_tailor.py` to create bundle & 2-page PDF |
| `tailored` | Application bundle & 2-page PDF verified on disk | Ready for `browser_apply_engine.py` |
| `applied` | Form submitted, full-page `receipt.png` saved | Application complete; synced to tracker |
| `needs_manual_review` | Mediator timed out (AFK), custom complex screener | Requires user to review `timeout_diagnostic.png` |
| `low_fit` | Scored $< 80\%$ against profile | Retained in DB for market intelligence |
| `out_of_region` | Located in US/EU requiring sponsorship | Excluded from active application loop |

---

## 4. The 1-by-1 Direct Apply & Firecrawl Cold Outreach Protocol

> **Approved Operational Directive**:
> Rather than relying on fragile end-to-end browser automation that can hit bot walls or timeouts, execution proceeds in an agile, high-leverage **1-by-1 human-in-the-loop cadence**.

### Target Scope & Seniority Filter
* **Target Audience**: **0–1 Year Experience / Junior / Entry-Level / Master's Graduate** AI, ML, Computer Vision, and Generative AI roles.
* **Skip Rule**: Automatically skip mid/senior roles requiring 3–5+ years of commercial AI experience unless explicitly instructed.

### The 7-Step Cadence for Each Job:
1. **Direct Application Link Resolution**:
   - Extract clean direct ATS portal links (Workable, Greenhouse, Lever, or official corporate careers portals) via Firecrawl alongside the original scraped LinkedIn URL to bypass bot walls.
2. **Sub-Second Tailored Resume Compilation**:
   - Compile 2-page LaTeX resume with Tectonic (`fast_ats_tailor.py`).
   - Strict 2-page invariant check via PyMuPDF.
3. **Resume vs. JD Alignment & Impact Audit**:
   - Cross-examine the compiled resume against the JD requirements.
   - Verify keyword coverage, project highlight positioning (e.g. KFUPM thesis, OCR, ViT, RAG), and strict adherence to `data/canonical_profile.json`.
   - Present transparent Alignment Audit Scorecard to candidate.
4. **Firecrawl Contact Intelligence**:
   - Identify active hiring managers, Engineering Directors, Practice Leads, and Talent Acquisition Recruiters.
   - Resolve verified corporate email patterns and LinkedIn profile URLs.
5. **Personalized Cold Outreach Pack**:
   - Provide copy-paste cold email draft and LinkedIn connection request note (<300 characters) referencing candidate's specific KFUPM research and automation background.
6. **Candidate Apply Gate & Interactive Feedback**:
   - Candidate opens link, submits tailored resume, sends cold email, and provides remarks / notes (e.g. screening questionnaire answers).
7. **Stateful Database Update & Follow-Up**:
   - Update SQLite database (`data/jobs.db`) with `status = 'applied'`, timestamp `applied_at`, and contact notes before queueing the next listing.

---

## 5. Master CLI Cockpit & Script Reference

AI Agents should invoke these scripts via shell commands:

```powershell
# 1. View overall pipeline metrics and queue health
python scripts/run_batch.py --status

# 2. Tailor resume for a specific job by ID (generates application folder & 2-page PDF)
python scripts/fast_ats_tailor.py --job-id <JOB_ID>

# 3. Update job status to applied with outreach notes in SQLite DB
python -c "import sqlite3, datetime; conn=sqlite3.connect('data/jobs.db'); cur=conn.cursor(); cur.execute('UPDATE jobs SET status=\'applied\', applied_at=?, notes=? WHERE id=?', (datetime.datetime.now().isoformat(), 'Applied via portal and sent cold email', '<JOB_ID>')); conn.commit()"
```

---

## 6. Official Skill Integrations

* **`career-ops`**: [`.agents/skills/career-ops/SKILL.md`](.agents/skills/career-ops/SKILL.md) — Reference implementation from [`career-ops-hq/career-ops`](https://github.com/career-ops-hq/career-ops). Provides Career-Ops Blocks A–H evaluation, LaTeX generation, and tracker management.
* **`job-hunter-firecrawl`**: [`.agents/skills/job-hunter-firecrawl/SKILL.md`](.agents/skills/job-hunter-firecrawl/SKILL.md) — Firecrawl search, scraping, and multi-portal decision-maker contact discovery.

