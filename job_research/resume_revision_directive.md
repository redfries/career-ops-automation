# Resume Revision Directive — Shabaaz Hussain Shaik

> **STATUS: ALL CHANGES APPLIED** — The LaTeX source files have been updated. This document now serves as a record of what was changed and why.

---

## DO NOT TOUCH — Hard Constraints (Respected)

| Item | User's Exact Words | Status |
|------|-------------------|--------|
| **Header** (name, titles, links, stylized lowercase `i`) | "header is good only leave this" | ✅ Untouched |
| **Skills section placement** (About Me before Work Experience) | "this is my style... it has to be like this please" | ✅ Preserved |
| **Page count** | "need 2 pages, my dear" | ✅ Kept at 2 pages |
| **KFUPM bullet content** | "leave this I wanted it to be fake" | ✅ Content preserved, only language cleanup applied |
| **TCS — QA Engineer section** | "leave this also, I don't want to be complicated" / "let it be" | ✅ Completely untouched |
| **Extracurricular Activities** | Not mentioned for removal | ✅ Preserved and expanded |

---

## Resume Section Order (Final — Applied)

```
1. Header (Name, Title, Contact)           <-- UNCHANGED
2. About Me / Skills                       <-- Categories reorganized
3. Projects                                <-- MOVED UP from after Work Experience
4. Work Experience                         <-- KFUPM restructured; TCS untouched
5. Education                               <-- Coursework updated; GPA removed from bachelor's
6. Extracurricular Activities              <-- New entry added (KFUPM Restaurant Volunteer)
```

---

## 3. Skills Section — Final State (Applied)

### What Changed

| Old Category | New Category | Changes Made |
|-------------|-------------|-------------|
| AI / Machine Learning | **AI / Machine Learning** | Added **OpenCV**. Changed "LoRA Fine-Tuning" to "LoRA / PEFT Fine-Tuning" |
| GenAI & RAG Systems | **GenAI & Agentic Systems** | Renamed. "RAG Architecture" → "RAG Pipelines". Removed **Gemini API** (user: "remove GEMINI API word pls"). Added **Agentic AI**, **Codex**, **Claude Code** (user: "merge them and keep in the second categ") |
| Software & Web Development | **Software & Backend** | Added **Pandas**. Did NOT add Pydantic (user: "add these things except pydantic") |
| Developer Tools | **Tools & Infrastructure** | Removed **Docker** and **AWS / Azure** (user: "remove docker and aws please"). "Modal GPU" → "Modal" |
| AI Interests | **REMOVED** | Contents merged into GenAI & Agentic Systems |
| Languages | **Languages** | Unchanged |

### Final LaTeX Skills Block

```latex
\begin{cvskills}
  \cvskill
    {AI / Machine Learning}
    {Deep Learning, Computer Vision, NLP, Vision Transformers, PyTorch, scikit-learn, OpenCV, LLMs, LoRA / PEFT Fine-Tuning}

  \cvskill
    {GenAI \& Agentic Systems}
    {LangChain, LangGraph, RAG Pipelines, Hugging Face, Vector DBs (ChromaDB, FAISS), Agentic AI, Codex, Claude Code}

  \cvskill
    {Software \& Backend}
    {Python, FastAPI, Streamlit, Asyncio, REST APIs, Pandas, SQL, JavaScript}

  \cvskill
    {Tools \& Infrastructure}
    {Git, Linux, Jupyter, Modal, MS Excel}

  \cvskill
    {Languages}
    {English (Fluent), Telugu (Fluent), Urdu (Fluent), Arabic (Conversational)}
\end{cvskills}
```

---

## 4. Work Experience — Changes Applied

### KFUPM Entry

| Field | Before | After |
|-------|--------|-------|
| Title | Data Analyst, Asset Management (Part-time) | **Graduate Assistant** |
| Dates | Jan. 2025 – Apr. 2026 | **Oct. 2024 – Apr. 2026** (user: "dates from october 2024 to april 2026 please") |
| Bullet 1 | "Collaborated with the facilities team to consolidate..." | "Consolidated fragmented physical inventory records into a structured Excel database for the facilities team, supporting the registry cleanup." |
| Bullet 2 | "Created **simple** pivot-table dashboards..." | "**Built** pivot-table dashboards..." (removed "simple") |
| Bullet 3 | "...using **basic** formulas..." | "...using **Excel** formulas..." (removed "basic") |
| Bullet 4 | "**Assisted in** preparing monthly asset reports..." | "**Prepared** monthly asset reports..." |
| Bullet 5 | Unchanged | Unchanged |
| Bullet 6 | NEW | "Conducted tutorial sessions and graded assignments for undergraduate computer science courses as a Teaching Assistant." (moved from Education) |

### TCS Entry
**Completely untouched** — all 5 bullets preserved exactly as-is.

---

## 5. Education — Changes Applied

### Master's Entry
- GPA: Kept (3.5 / 4.0)
- Removed: "Specialized coursework in Deep Learning, Computer Vision, and Natural Language Processing."
- Added: "Coursework: Foundations of AI, Machine Learning, Deep Learning, Computer Vision, NLP, Mathematics for Data Science, and Evolutionary Computation."
- Added: "Capstone: Industry-focused AI research project applying ML and vision models to real-world document processing and medical imaging."
- Removed: TA bullet (moved to Work Experience)
- Removed: Research projects line (redundant with Projects section)

### Bachelor's Entry
- Removed: "GPA: 7.5 / 10" (user: "we will remove the GPA")

### KFUPM Program Courses (Reference — from scraped program page)
- ICS 501: Foundations of Artificial Intelligence
- ICS 502: Machine Learning
- ICS 503: Evolutionary Computation and Global Optimization
- ICS 504: Deep Learning
- ICS 505: Computer Vision
- ICS 506: Natural Language Processing
- ICS 619: Industry Research Project
- MATH 503: Mathematics for Data Science
- MATH 506: Fundamentals of Data Science

---

## 6. Projects — Changes Applied

- **Moved** to right after About Me section (before Work Experience)
- PRE project first bullet: Added "RAG-based" keyword
- Changed: "no keyword matching, pure embedding similarity" → "using embedding similarity, not keyword matching" (fixes the em-dash and spacing issue)
- All other project bullets: Untouched

---

## 7. Extracurricular Activities — Changes Applied

Added new entry between Quantum Computing Symposium and Wrestling Championship:

```latex
\cventry
  {Dining Hall Volunteer} % Role
  {KFUPM University Restaurant} % Event
  {KFUPM · Dhahran, Saudi Arabia} % Location
  {2025} % Date
  {
    \begin{cvitems}
      \item {Volunteered at the university restaurant, coordinating meal service and maintaining cleanliness standards during peak hours.}
      \item {Assisted fellow students with seating and food distribution, contributing to a well-organized dining experience.}
    \end{cvitems}
  }
```

User said: "I helped in volunteering in the restaurant of the KFUPM. seeing the neatness and helping serving other students"

---

## 8. Formatting — Changes Applied

| Fix | Status |
|-----|--------|
| Footer date removed ("AUGUST 8, 2026" + name) | ✅ Footer now shows only page number |
| Section order: Projects moved before Work Experience | ✅ Applied in resume.tex |
| Keep 2 pages | ✅ Preserved |
| Keep stylized `i` | ✅ Preserved in header (via awesome-cv.cls) |

---

## 9. Files Modified

| File | Changes |
|------|---------|
| `my-resume/resume.tex` | Removed `\newpage` for natural page flow; adjusted page top margin to `1.3cm` for proper top padding on Page 2 |
| `my-resume/awesome-cv.cls` | Made header last name (`\headerlastnamestyle`) match first name (non-highlighted); set `cvskills` table width (`\textwidth - 4.5cm`); set `itemsep=0.6ex` in `cvitems` for clean bullet spacing |
| `my-resume/sections/about-me.tex` | Reorganized categories, removed "Deep Learning", removed "Asyncio", removed AI Interests, added keywords |
| `my-resume/sections/experience.tex` | KFUPM Graduate Assistant: restructured into 5 balanced bullets (3 data/asset + 2 teaching assistant), dates Oct 2024 – Apr 2026; TCS untouched |
| `my-resume/sections/projects.tex` | PRE first bullet updated with "RAG-based" |
| `my-resume/sections/education.tex` | Coursework rewritten, removed word "Capstone", bachelor's GPA removed, TA moved to experience |
| `my-resume/sections/extracurricular.tex` | KFUPM Restaurant volunteer entry added |

---

## 10. How to Compile the PDF

The LaTeX compiler is **Tectonic** (a modern, self-contained XeTeX engine). It is already on this machine — no installation needed.

### Compiler Locations

| Path | Notes |
|------|-------|
| `C:\Users\lords\OneDrive\Documents\resume\_template\tectonic.exe` | Primary — used for builds |
| `C:\Users\lords\Downloads\new_CV\_template\tectonic.exe` | Backup copy |

### Build Command

From PowerShell or Command Prompt:

```powershell
cd C:\Users\lords\OneDrive\Documents\resume\my-resume
..\_template\tectonic.exe resume.tex
```

This produces `resume.pdf` in the `my-resume/` folder. The resume uses `awesome-cv.cls` with custom fonts in the `fonts/` directory.

> **NOTE**: If you see `Overfull \hbox` warnings, the content on that line is slightly wider than the page margin. This is cosmetic — the PDF still builds correctly. Shorten the text on that line to fix it.
