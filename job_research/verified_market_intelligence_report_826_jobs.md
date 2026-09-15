# Verified Market Intelligence & Pipeline Report (826 Clean Jobs)
**Audit & Cleanup Date**: September 14, 2026  
**Candidate**: Shabaaz Hussain Shaik (MS in AI, KFUPM Dhahran)  
**Database**: [`data/jobs.db`](file:///c:/Users/lords/OneDrive/Documents/career-ops-automation/data/jobs.db) (SQLite verified source of truth)  
**Backup**: `data/jobs.db.bak`

---

## 1. Executive Summary & Data Integrity Audit

Following an in-depth audit of the scraped database and ingestion pipelines, the raw dataset was purged of corrupt entries, missing IDs were deterministic-mapped, un-ingested duplicates were resolved, and candidate-tailored match scoring was executed.

### Database Remediation Breakdown:
1. **Purged Corrupt Scrapes (71 Naukrigulf rows)**:
   - 100% of Naukri listings lacked job descriptions (`description_text = ''`).
   - Markdown parsing regex had captured login navigation text, tracking URLs, and invalid company names (`- 1 - 6 Years`).
2. **Deterministic Primary Keys Backfilled (261 rows)**:
   - Bayt (173) and Indeed (88) had been inserted with `id IS NULL`.
   - All rows now possess verified deterministic primary keys (`bayt_<jobid>`, `indeed_<jk>`).
3. **LinkedIn Scrape Reconciliation**:
   - `data/fresh_linkedin_jobs.json` had 670 rows, with 558 in the database.
   - The 112 un-ingested items were verified to be identical `(company, title)` duplicate reposts (e.g., TELUS Digital reposting the same role 12 times across GCC cities), correctly protected by `UNIQUE INDEX idx_company_title`.
4. **Geographic Isolation of US Roles (173 jobs)**:
   - Isolated and tagged 173 United States postings with `status = 'out_of_region'` because the candidate requires H-1B/O-1 visa sponsorship to work in the US.
5. **Career-Ops Match Scoring Executed (0–100%)**:
   - Evaluated role titles, required tech stacks, experience levels, and work authorization fit against candidate's canonical profile.
   - **40 jobs Shortlisted** (Score >= 75%)
   - **204 jobs Evaluated / Moderate Fit** (Score 50–74%)
   - **409 jobs Low Fit** (Score < 50%)
   - **173 jobs Out of Region** (US Location - Ineligible)

---

## 2. Portal & Geographic Distribution (Clean Database)

| Portal | Clean Records | % of DB | Status | Description Quality |
| :--- | :--- | :--- | :--- | :--- |
| **LinkedIn** | 565 | 68.4% | 100% Scored | Full descriptions (avg 4,538 chars) |
| **Bayt.com** | 173 | 20.9% | 100% Scored | Search snippets (avg 680 chars) |
| **Indeed (KSA/UAE)** | 88 | 10.7% | 100% Scored | Search snippets (avg 679 chars) |
| **Naukrigulf** | 0 | 0.0% | Purged | Purged corrupt/empty listings |
| **TOTAL** | **826** | **100%** | **Clean** | **All records have primary keys & scores** |

### Verified Geographic Breakdown:
* **UAE (Dubai / Abu Dhabi)**: 440 jobs (53.3%)
* **Saudi Arabia (Direct Iqama Transfer / Resident)**: 212 jobs (25.7%)
  * Riyadh: 140
  * Eastern Province (Dhahran / Khobar / Dammam): 32
  * Western Province (Jeddah / Mecca): 19
  * General KSA / Multi-city: 21
* **Remote (Global / Contractor)**: 1 job (0.1%)
* **United States (Tagged `out_of_region`)**: 173 jobs (20.9%)

---

## 3. Empirical Tech Stack Demand (Across Clean Dataset)

| Technology / Skill | Frequency | Demand % | Profile Alignment for Shabaaz |
| :--- | :--- | :--- | :--- |
| **Python** | 371 | **44.9%** | **Direct Match** (Candidate primary language) |
| **LLMs & Generative AI** | 293 | **35.5%** | **Direct Match** (Gemini API, RAG, LoRA, Qwen3.5) |
| **Cloud (AWS / Azure / GCP)** | 257 | **31.1%** | **Supported** (Modal GPU, FastAPI, cloud deployments) |
| **Data Analytics / BI (PowerBI/Tableau)** | 214 | **25.9%** | **Supported** (Pandas, SQL, KFUPM Graduate Assistant reporting) |
| **Agentic AI & Orchestration** | 193 | **23.4%** | **High Priority** (LangChain, LangGraph, tool agents) |
| **MLOps & Pipelines** | 164 | **19.9%** | **Supported** (FastAPI, Docker microservices) |
| **PyTorch** | 135 | **16.3%** | **Direct Match** (Candidate deep learning foundation) |
| **SQL** | 127 | **15.4%** | **Direct Match** (Relational databases, queries) |
| **Prompt Engineering & Fine-tuning** | 124 | **15.0%** | **Direct Match** (LoRA, PEFT, prompt design) |
| **NLP / Text Processing** | 113 | **13.7%** | **Direct Match** (Sentence embeddings, OCR tokenization) |
| **RAG (Vector Databases)** | 111 | **13.4%** | **Direct Match** (Personalized Reading Experience project) |
| **Docker / Containers** | 86 | **10.4%** | **Direct Match** (Containerization, Modal deployment) |
| **Computer Vision (OpenCV / YOLO / ViT)** | 63 | **7.6%** | **Direct Match** (Arabic Cheque OCR, Retinal ViT research) |

---

## 4. Top 15 Shortlisted Opportunities (KSA & UAE)

| Portal | Role Title | Company | Location | Match Score | Key Strengths |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LinkedIn** | Manager - FWA AI Engineer | Bupa Arabia | Jeddah, Saudi Arabia | **93.0%** | Applied AI, GenAI, Python |
| **LinkedIn** | Applied AI Engineer | Fuse Energy | Dubai, UAE | **93.0%** | Python, asyncio, PyTorch, Docker |
| **LinkedIn** | AI Engineer | MOZN | Riyadh, Saudi Arabia | **91.0%** | Deep Learning, NLP, PyTorch, KSA leader |
| **LinkedIn** | AI Engineer - Computer Vision | InnovationTeam | Riyadh, Saudi Arabia | **89.0%** | Computer Vision, OpenCV, PyTorch |
| **LinkedIn** | Junior AI Engineer | InnovationTeam | Riyadh, Saudi Arabia | **89.0%** | Entry-level AI, Python, ML pipelines |
| **LinkedIn** | Data Scientist | Melon Digital Insurance | Dammam, Eastern Province | **88.0%** | Local to Dhahran/KFUPM, predictive models |
| **LinkedIn** | AI Engineering, Intern | Bain & Company | Dubai / Riyadh | **88.0%** | Prestigious tier-1 consulting AI practice |
| **LinkedIn** | AI Engineer Intern – Vision-Language Models | TowardsChange | Dubai, UAE | **88.0%** | VLM fine-tuning (Qwen/LoRA alignment) |
| **LinkedIn** | AI Engineer (Remote) | Hired | UAE / Remote | **88.0%** | Remote AI engineering, GenAI pipelines |
| **LinkedIn** | Senior Machine Learning Engineer | cander | Abu Dhabi, UAE | **87.0%** | ML modeling, PyTorch |
| **LinkedIn** | AI Engineer | InnovationTeam | Riyadh, Saudi Arabia | **86.0%** | Applied ML, REST APIs |
| **LinkedIn** | AI Engineer – GenAI and Automation | MultiBank Group | Dubai, UAE | **85.0%** | GenAI, workflow automation |
| **LinkedIn** | Forward Deployed AI/ML Expert | SAP | Riyadh, Saudi Arabia | **84.0%** | Enterprise AI solutions |
| **LinkedIn** | Machine Learning Engineer | ai71 | Abu Dhabi, UAE | **82.0%** | Falcon LLM ecosystem, PyTorch |
| **LinkedIn** | AI/ML Engineer - Industrial Analytics | Tata Consultancy Services | Riyadh, Saudi Arabia | **81.0%** | Industrial ML, KSA client deployment |
