# 🎯 Career-Ops Automation Engine

An autonomous, deterministic job application automation system designed for AI & Machine Learning engineers. Built to replace brittle conversational agent loops with an **n8n-style stateful pipeline**: fail-fast invariants, persistent browser sessions, strict candidate provenance, and human-in-the-loop **Mediator Mode**.

---

## 🏛️ System Architecture

```
                                  [ data/jobs.db ] (SQLite State Store)
                                        │
                                        ├── Status: shortlisted (Score >= 80)
                                        ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ 1. ATS RESUME TAILORING ENGINE (scripts/fast_ats_tailor.py)                            │
 │    • Ingests job posting & canonical_profile.json                                      │
 │    • Extracts domain keywords (e.g. ViT, PyTorch, LangChain, RAG)                     │
 │    • Dynamically tailors Awesome-CV LaTeX master source in my-resume/                 │
 │    • Compiles via Tectonic engine in ~3.5s                                             │
 │    • Hard assertion: Enforces STRICT 2-PAGE PDF (PyMuPDF fitz)                         │
 │    • Exports application bundle to applications/<date>_<company>_<job_id>/             │
 └──────────────────────────────────────┬─────────────────────────────────────────────────┘
                                        │
                                        ├── Status: tailored
                                        ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │ 2. BROWSER SUBMITTER & MEDIATOR (scripts/browser_apply_engine.py)                      │
 │    • Connects to persistent Chrome context (data/browser_profile)                      │
 │    • Navigates to job application portal (LinkedIn Easy Apply, Greenhouse, Lever, etc.)│
 │    • Autofills standard fields (Name, Email, Phone, Location, Work Rights)             │
 │    • Attaches verified 2-page resume.pdf in ~150ms                                     │
 │    • SUPERVISOR / MEDIATOR LOOP:                                                       │
 │       ├─ Standard flow: Form completes & submits in ~10 seconds                        │
 │       └─ Complex screener / CAPTCHA: Chime alert + 45s countdown timer                 │
 │            ├─ Human mediates & presses Enter -> Completes submission                   │
 │            └─ Human AFK (timer expires) -> Saves timeout_diagnostic.png, marks         │
 │               status='needs_manual_review', closes tab, smoothly advances             │
 └──────────────────────────────────────┬─────────────────────────────────────────────────┘
                                        │
                         ┌──────────────┴──────────────┐
                         ▼                             ▼
               Status: applied           Status: needs_manual_review
           (receipt.png saved)           (diagnostic screenshot saved)
```

---

## ⚡ Key Highlights & Core Invariants

### 1. No 30-Minute Agent Hangs
Agents previously drifted into endless conversational loops or hung indefinitely on complex web forms. This engine enforces hard execution timeouts:
* Maximum 90-second overall browser deadline.
* 45-second Mediator supervisor countdown.
* If user is away, it captures a diagnostic screenshot, updates SQLite to `needs_manual_review`, and **advances to the next job in the batch without crashing**.

### 2. Strict 2-Page Resume Policy
* All generated resumes are strictly locked to **2 pages** (based on the candidate's master Awesome-CV LaTeX source).
* PyMuPDF (`fitz`) performs a hard runtime check: if page count != 2, compilation aborts immediately. Margins and section hierarchies are strictly preserved.

### 3. Strict Candidate Provenance (Zero Hallucination)
* All data originates strictly from [`data/canonical_profile.json`](data/canonical_profile.json).
* Candidate: **Shabaaz Hussain Shaik** (Dhahran, Saudi Arabia).
* Education: **KFUPM MS in AI** (BRAIN Lab).
* Commercial Experience: **TCS QA Automation Engineer** (Salesforce test automation, Tosca, Python).
* **Hard Invariant**: Never claims commercial AI engineering at TCS. AI experience is exclusively academic and research-driven.
* Saudi Arabia Work Rights: Resident on **Transferable Iqama** (no visa sponsorship required).

### 4. Official Career-Ops Skill Integration
* Integrates the official skill specification from [`career-ops-hq/career-ops`](https://github.com/career-ops-hq/career-ops).
* Skill router installed at [`.agents/skills/career-ops/SKILL.md`](.agents/skills/career-ops/SKILL.md) and paired with [`.agents/skills/job-hunter-firecrawl/SKILL.md`](.agents/skills/job-hunter-firecrawl/SKILL.md).

---

## 📂 Workspace Organization

```
career-ops-automation/
├── AGENT_SOP.md                 # Master Standard Operating Procedure for AI agents
├── README.md                    # System architecture & documentation
├── .agents/
│   └── skills/
│       ├── career-ops/          # Official career-ops skill (Blocks A-H)
│       └── job-hunter-firecrawl/# Firecrawl multi-portal job hunter
├── applications/                # Tailored application bundles (gitignored)
│   └── YYYY-MM-DD_<company>_<job_id>/
│       ├── job_details.json
│       ├── application_package.json
│       ├── submission_manifest.json
│       ├── resume.pdf           # Verified 2-page ATS resume
│       ├── dry_run_preview.png  # (From dry-run)
│       └── receipt.png          # (From confirmed submission)
├── data/
│   ├── canonical_profile.json   # Authoritative source of candidate truth
│   ├── canonical_profile.md     # Markdown mirror of candidate profile
│   ├── jobs.db                  # SQLite database tracking all 800+ job states
│   └── browser_profile/         # Persistent Chrome user data & session cookies
├── my-resume/                   # Master LaTeX template (Awesome-CV)
│   ├── resume.tex
│   ├── awesome-cv.cls
│   └── sections/
└── scripts/
    ├── run_batch.py             # Master CLI cockpit for batch operations
    ├── fast_ats_tailor.py       # Deterministic LaTeX tailoring & PDF compiler
    └── browser_apply_engine.py  # Playwright browser submitter with Mediator
```

---

## 🚀 Quickstart & CLI Cockpit

All operations can be managed via the unified batch cockpit:

### 1. View Pipeline Status
Inspect active application queues and state breakdown across all scraped jobs:
```powershell
python scripts/run_batch.py --status
```

### 2. Tailor Resumes in Batch
Tailor application bundles and 2-page PDFs for the top $N$ shortlisted jobs:
```powershell
python scripts/run_batch.py --tailor 5
```

### 3. Tailor a Specific Job
```powershell
python scripts/fast_ats_tailor.py --job-id 4460970498
```

### 4. Run Browser Submitter in Assisted Mode (with Mediator)
Launches the persistent Chrome browser, auto-fills standard details, attaches the 2-page resume, and summons the user if human mediation is required:
```powershell
python scripts/run_batch.py --apply 3 --mode assisted
```

### 5. Safe Dry-Run (Verification Mode)
Opens the job application portal, fills fields, uploads resume, captures a full-page verification screenshot (`dry_run_preview.png`), and closes without clicking Submit:
```powershell
python scripts/browser_apply_engine.py --job-id 4460970498 --mode dry-run
```

---

## 📊 Database State Machine

Jobs in `data/jobs.db` cycle through the following deterministic states:

| Status | Description | Trigger / Transition |
| :--- | :--- | :--- |
| `shortlisted` | Fit score $\ge 80\%$ | Scored by evaluation filter |
| `tailored` | Application bundle + 2-page PDF verified on disk | `fast_ats_tailor.py` |
| `applied` | Submitted via browser; `receipt.png` captured | `browser_apply_engine.py` |
| `needs_manual_review` | Complex screener / CAPTCHA timed out (AFK) | Mediator supervisor fallback |
| `low_fit` | Fit score $< 80\%$ | Archived for market insights |
| `out_of_region` | Requires US/EU visa sponsorship | Excluded from application queue |

---

## 🤖 AI Agent Guidelines

If you are an AI agent (Claude Code, Antigravity, Gemini, Codex) assisting the user in this repository, **read [`AGENT_SOP.md`](AGENT_SOP.md) before executing any task**. 

* Never modify the 2-page resume layout into 1 page.
* Never fabricate commercial AI roles at TCS.
* Use `run_batch.py` rather than running ad-hoc, unmonitored scripts.
