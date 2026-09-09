# Career-Ops AI Job Copilot (Chrome & Edge Extension)

> **Sub-Second ATS Tailoring, Form Autofill & Antigravity Local Hub Bridge**

The **Career-Ops AI Job Copilot** is a Manifest V3 browser extension for Google Chrome, Microsoft Edge, and Chromium-based browsers. It connects your live job browsing directly to Antigravity's ATS resume tailoring engine, SQLite database (`data/applications.db`), and Notion application tracker.

---

## Architecture Overview

```
 ┌─────────────────────────────────────────────────────────────┐
 │                      User Browser                           │
 │  Greenhouse / Lever / Ashby / LinkedIn / Bayt Job Posting   │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │           Career-Ops Copilot Extension (MV3)                │
 │  - content_scripts/extractor.js (React/Remix DOM Reader)    │
 │  - popup/popup.html + popup.js (3-Stage HITL UI & Toasts)   │
 └──────────────────────────────┬──────────────────────────────┘
                                │ HTTP API (localhost:8765)
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │            Local Command Hub (scripts/local_server.py)      │
 │  - POST /api/check-job (Smart deduplication & state recovery)│
 │  - POST /api/evaluate  (10ms keyword match & ATS scoring)   │
 │  - POST /api/tailor    (Sub-second ATS resume compilation)  │
 │  - GET  /api/pdf       (Direct inline Chrome PDF streaming) │
 │  - POST /api/open-folder (Native Windows Explorer launcher) │
 │  - POST /api/mark-applied (SQLite & Notion submission gate) │
 └──────────────────────────────┬──────────────────────────────┘
                                │
               ┌────────────────┴────────────────┐
               ▼                                 ▼
      SQLite Storage                     Notion Database
   (data/applications.db)           (Career-Ops Job Applications)
```

---

## Key Features

1. **Smart Deduplication & Revisit Recovery**:
   - As soon as you open the extension on any job page, it queries `/api/check-job`.
   - If the job was already evaluated, tailored, or applied:
     - **Submitted**: Displays `✅ Application Submitted & Tracked` with confirmation receipt #, timestamp, and ATS score.
     - **Tailored**: Displays `⚡ Application Tailored & Ready` with existing match score, archetype, and quick-action tools.
     - **Zero Redundant Folders**: Does not duplicate files or re-run tailoring unless explicitly requested via `🔄 Force Re-tailor`.
2. **Sub-Second ATS Resume Compilation**:
   - Generates single-column, ATS-safe semantic HTML resumes.
   - Compiles via headless Edge/Chromium engine with sub-second execution.
   - Ranks candidate evidence bullets to match target role keywords with zero hallucination.
3. **Interactive PDF Streaming & Explorer Launch**:
   - **`📄 View PDF (Tab)`**: Serves the generated PDF via `/api/pdf` directly into a new browser tab for immediate viewing.
   - **`📁 Open Folder`**: Opens the application bundle directory in Windows Explorer.
4. **React & Remix-Compatible 1-Click Form Autofill**:
   - Uses prototype property setters (`setNativeValue`) to update React/Remix controlled input state on Greenhouse, Lever, and Ashby forms.
   - Fills First Name, Last Name, Preferred Name, Email, Phone, LinkedIn, GitHub, Portfolio, Education, and standard Screener Answers.
   - Features dynamic script auto-injection (`ensureContentScriptReady`) to prevent connection failures.
5. **Strict Submission Gate**:
   - Prevents unverified applications from polluting Notion or SQLite.
   - Only moves to `submitted` status after you click **`✅ Mark as Applied`** with an optional confirmation receipt #.

---

## Installation & Setup

### 1. Start the Local Command Hub
The extension communicates with the local Python server on `http://127.0.0.1:8765`:

```bash
# From workspace root
python -u scripts/local_server.py
```

### 2. Load the Extension in Chrome or Edge
1. Open your browser and navigate to:
   - Chrome: `chrome://extensions`
   - Edge: `edge://extensions`
2. Enable **Developer mode** (toggle switch in the top-right corner).
3. Click **Load unpacked** (or **Load unpacked extension**).
4. Select the `browser_extension` directory inside this repository:
   ```
   c:\Users\lords\OneDrive\Documents\career-ops-automation\browser_extension
   ```
5. Pin the **Career-Ops AI Job Copilot** icon to your browser toolbar.

---

## Complete API Reference (Local Command Hub)

Base URL: `http://127.0.0.1:8765`

### `GET /api/health`
Returns server status and currently active job session.
```json
{
  "status": "online",
  "service": "Career-Ops Command Hub",
  "version": "1.0.0",
  "active_job": { ... }
}
```

### `POST /api/check-job`
Checks if a URL, company, or role already exists in SQLite or `applications/`.
* **Payload**: `{"url": "https://...", "company": "LLR Partners", "role": "Forward Deployed Engineer"}`
* **Response**:
```json
{
  "exists": true,
  "application": {
    "id": "2026-09-10_target-employer_forward-deployed-engineer",
    "company": "Target Employer",
    "role": "Forward Deployed Engineer",
    "status": "prepared",
    "ats_score": 88.9,
    "archetype": "rag",
    "pdf_path": "C:\\...\\resume.pdf",
    "bundle_dir": "C:\\...\\applications\\..."
  }
}
```

### `POST /api/evaluate`
Lightweight keyword evaluation (~10ms). Zero files created, zero DB clutter.
* **Payload**: `{"company": "...", "role": "...", "jd_text": "...", "focus": "auto"}`
* **Response**: `{"success": true, "ats_score": 88.9, "archetype": "rag", "matched_keywords": [...], "missing_keywords": [...]}`

### `POST /api/tailor`
Compiles tailored ATS PDF, stores bundle in `applications/`, upserts to SQLite, and syncs to Notion.
* **Payload**: `{"company": "...", "role": "...", "jd_text": "...", "url": "...", "sync": true}`
* **Response**: `{"success": true, "application_id": "...", "pdf_path": "...", "bundle_dir": "...", "screener_answers": {...}}`

### `GET /api/pdf?path=<encoded_pdf_path>`
Streams binary PDF with `Content-Type: application/pdf` and `inline` disposition. Opens natively in Chrome/Edge.

### `POST /api/open-folder`
Launches Windows File Explorer pointing directly to the target application directory.
* **Payload**: `{"bundle_dir": "C:\\path\\to\\bundle"}`

### `POST /api/mark-applied`
Strict submission gate: commits status as `submitted` in SQLite, regenerates `active_application_tracker.md`, and updates Notion status to `submitted`.
* **Payload**: `{"application_id": "...", "receipt": "CONF-12345"}`

---

## Directory Structure

```
browser_extension/
├── manifest.json              # Chrome MV3 manifest with scripting & activeTab
├── README.md                  # Authoritative extension documentation
├── icons/                     # 16px, 48px, 128px high-contrast icons
├── content_scripts/
│   └── extractor.js           # DOM job extractor & React/Remix native form filler
└── popup/
    ├── popup.html             # Sleek dark-mode HITL UI with toasts & badges
    ├── popup.css              # Custom styling, transitions & animations
    └── popup.js               # State manager, API bridge & event handlers
```
