# Combined Market Intelligence Report (897 Jobs)
**Generated**: September 14, 2026  
**Target Scope**: 0–1 Year Experience / Entry-Level / Freshers / Graduates / Interns  
**Geographies Covered**: Saudi Arabia (Riyadh, Eastern Province, Jeddah), UAE (Dubai, Abu Dhabi), and Regional GCC  
**Portals Ingested**: LinkedIn (via Apify), Bayt, Indeed, and Naukrigulf (via Firecrawl Stealth)  
**Database**: [`data/jobs.db`](file:///c:/Users/lords/OneDrive/Documents/career-ops-automation/data/jobs.db) (SQLite, single local source of truth)

---

## Executive Summary: Where You Stand

As a fresh Master's graduate from **KFUPM (Dhahran)** looking to land a role quickly in the current AI landscape, this data provides clarity.

Across **897 fully deduplicated, entry-level jobs**:
1. **The Core Filter**: More than **32.8% of entry-level postings specifically ask for LLM / Generative AI familiarity**, and **21.7% mention Agentic AI / AI Orchestration** (LangChain, LangGraph, CrewAI, LlamaIndex).
2. **The "Fresher Reality" in the GCC**: Traditional ML algorithms (Scikit-Learn, Random Forests, SVMs) represent only 6.1% of listed demand. Today's entry-level recruiters expect freshers to understand **Applied AI Engineering**: taking foundation models, adding **RAG pipelines**, and deploying them with **Python + FastAPI + Docker** on Cloud.
3. **Regional Hotspots**:
   - **UAE (Dubai / Abu Dhabi)**: 57.0% of total volume (high concentration of AI startups, global tech firms, and regional innovation hubs).
   - **Saudi Arabia (Riyadh & Eastern Province)**: 22.8% of direct jobs (SDAIA, Master-Works, NEOM, Aramco/KFUPM ecosystem, and national digital transformation mandates).

---

## 1. Multi-Portal Distribution & Deduplication Stats

| Portal | Raw Scraped | Duplicates / Cross-posts Dropped | Net Unique Jobs in DB | % of Total Database |
| :--- | :--- | :--- | :--- | :--- |
| **LinkedIn** | 670 | 105 | **565** | 63.0% |
| **Bayt.com** | 225 | 52 | **173** | 19.3% |
| **Indeed (KSA/UAE)** | 148 | 60 | **88** | 9.8% |
| **Naukrigulf** | 123 | 52 | **71** | 7.9% |
| **TOTAL** | **1,166** | **269** | **897** | **100%** |

*Note: All cross-portal clones (e.g. Master-Works or InnovationTeam advertising simultaneously on Bayt, Indeed, and LinkedIn) were automatically detected and deduped via `(company, title)` normalization.*

---

## 2. Empirical Tech Stack Rankings (Entry-Level 2026)

| Skill / Technology | Frequency | Market Demand % | Strategic Priority for Freshers |
| :--- | :--- | :--- | :--- |
| **Python** | 371 | **41.4%** | **Essential**: The non-negotiable lingua franca. |
| **LLMs & Generative AI** | 294 | **32.8%** | **Must-Have**: Prompting, API integration, token economics. |
| **Cloud (AWS / Azure / GCP)** | 258 | **28.8%** | **Differentiator**: Deploying models, Cloud run, S3, Azure AI. |
| **BI & Data Analytics (PowerBI/Tableau)** | 216 | **24.1%** | **High**: Enterprise employers want business insights alongside AI. |
| **Agentic AI & Orchestration** | 195 | **21.7%** | **Highest Surge**: LangChain, LangGraph, tool-calling agents. |
| **MLOps & Pipelines** | 164 | **18.3%** | **Key Edge**: CI/CD, model monitoring, automated workflows. |
| **PyTorch** | 135 | **15.1%** | **Core Academic**: Fine-tuning, custom training, vision/NLP models. |
| **SQL** | 127 | **14.2%** | **Essential**: Querying enterprise data layers and relational DBs. |
| **Prompt Engineering & Fine-tuning** | 124 | **13.8%** | **Practical**: LoRA, PEFT, prompt optimization techniques. |
| **TensorFlow / Keras** | 114 | **12.7%** | **Legacy / Corporate**: Maintenance of older enterprise models. |
| **NLP / Text Processing** | 113 | **12.6%** | **Domain**: Tokenization, embedding vector spaces, parsing. |
| **RAG (Vector DBs: Chroma/Pinecone/FAISS)** | 111 | **12.4%** | **Core Architecture**: Hybrid search, semantic chunking. |
| **Deep Learning (Architectures)** | 96 | **10.7%** | **Foundational**: CNNs, Transformers, attention mechanisms. |
| **Docker / Containers** | 86 | **9.6%** | **Production**: Packaging microservices cleanly for deployment. |
| **Computer Vision (OpenCV / YOLO)** | 63 | **7.0%** | **Specialized**: Inspection, OCR, object detection in industrial KSA. |

---

## 3. Role Archetypes (What Companies Call These Jobs)

1. **AI / Data Intern or Graduate Trainee (20.1% - 180 jobs)**:
   - High willingness to train fresh Master's graduates.
   - Frequent titles: *Graduate AI Engineer, AI Intern, Data Science Fellow, Tamheer Intern (KSA)*.
2. **AI Engineer / GenAI Specialist (13.3% - 119 jobs)**:
   - Focused on building applications on top of LLMs and foundation models.
3. **Machine Learning / Deep Learning Engineer (12.2% - 109 jobs)**:
   - Hands-on modeling, fine-tuning, training scripts in PyTorch.
4. **Data Scientist (9.0% - 81 jobs)**:
   - Predictive modeling, statistical analysis, and enterprise decision science.
5. **Computer Vision & Specialized AI (8.9% - ~80 jobs)**:
   - Smart city, surveillance, video analytics, and manufacturing QC.

---

## 4. The 3-Pillar Strategy for Your Resume & Portfolio

Given your KFUPM academic background and the exact requirements from these 897 jobs:

### Pillar 1: Don't Pitch as a "Generalist Fresher"
Recruiters get hundreds of resumes stating *"passionate fresher looking for an opportunity."* Instead, position yourself as an:
> **"AI Engineer specializing in Agentic Systems & Production RAG Pipelines (KFUPM MSc)"**

### Pillar 2: The Two Benchmark Projects That Check 80% of Job Requirements
Employers are hiring entry-level candidates who have built end-to-end applications rather than just Jupyter Notebooks:
- **Project 1: Multi-Agent Enterprise Research Assistant**
  - **Stack**: LangGraph / LangChain + FastAPI + Qdrant/Chroma vector DB + Llama-3/Gemini.
  - **Covers**: Agentic AI (21.7%), LLMs (32.8%), RAG (12.4%), Python (41.4%).
- **Project 2: Vision-Language Inspection or Document Extraction Tool**
  - **Stack**: PyTorch + YOLOv8 or LayoutLM + Docker container deployed on AWS/Azure.
  - **Covers**: PyTorch (15.1%), Computer Vision (7.0%), Docker (9.6%), Cloud (28.8%).

### Pillar 3: Location Arbitrage (KSA & UAE Dual-Track)
- Keep your home base in **Saudi Arabia** (leverage KFUPM's prestige in Riyadh, Aramco, and Eastern Province).
- Target **UAE remote or relocation-supported graduate programs** simultaneously (57% of regional volume is based out of Dubai/Abu Dhabi).
