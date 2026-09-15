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

## 4. The "Mediator Mode" Human-in-the-Loop Protocol

When running `browser_apply_engine.py`:
1. **Persistent Browser Session**: Attaches to `data/browser_profile` (or user's Chrome data dir) where login cookies for LinkedIn and boards persist.
2. **Fast Autofill**: Fills Name, Email, Phone, Location, Work Rights, and attaches `resume.pdf` in under 2 seconds.
3. **Mediator Alert**: If an unexpected screener question, dynamic dropdown, or CAPTCHA appears:
   * Plays an audible chime (`\a`).
   * Starts a **45-second countdown timer** in the terminal.
   * If the user mediates in the open Chrome window and presses `[ENTER]`: Resumes and completes the application.
   * If the user is away (timer expires):
     * Captures `applications/<folder>/timeout_diagnostic.png`.
     * Updates database: `status = 'needs_manual_review'`.
     * Closes the tab cleanly.
     * **Smoothly advances to the next job without crashing or stopping the batch loop.**

---

## 5. Master CLI Cockpit Reference

AI Agents should invoke these scripts via shell commands:

```powershell
# 1. View overall pipeline metrics and queue health
python scripts/run_batch.py --status

# 2. Tailor resumes for top N shortlisted jobs (generates folders & 2-page PDFs)
python scripts/run_batch.py --tailor 5

# 3. Tailor a specific job by ID
python scripts/fast_ats_tailor.py --job-id 4460970498

# 4. Run browser application loop in Assisted Mode (with Mediator supervisor)
python scripts/run_batch.py --apply 3 --mode assisted

# 5. Run a safe dry-run (fills form, attaches resume, captures preview screenshot, skips submit)
python scripts/browser_apply_engine.py --job-id 4460970498 --mode dry-run
```

---

## 6. Official Skill Integrations

* **`career-ops`**: [`.agents/skills/career-ops/SKILL.md`](.agents/skills/career-ops/SKILL.md) — Reference implementation from [`career-ops-hq/career-ops`](https://github.com/career-ops-hq/career-ops). Provides Career-Ops Blocks A–H evaluation, LaTeX generation, and tracker management.
* **`job-hunter-firecrawl`**: [`.agents/skills/job-hunter-firecrawl/SKILL.md`](.agents/skills/job-hunter-firecrawl/SKILL.md) — Firecrawl search, scraping, and multi-portal ingestion.
