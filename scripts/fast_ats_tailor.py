#!/usr/bin/env python3
"""
fast_ats_tailor.py
Sub-Second ATS Resume Tailoring & Validation Engine:
- In-memory keyword extraction, scoring, and archetype detection (< 50ms)
- Deterministic bullet ranking & project reordering (< 10ms)
- Instant single-column ATS PDF rendering via native Windows Edge (< 300ms)
- Multi-step PDF validation via PyMuPDF (headers, text streams, page count)
- Automatic SQLite registration & Markdown tracker export
- Optional 1-click Notion synchronization
- Block H ATS Screener form answers generation
"""

import os
import sys
import re
import time
import json
import shutil
import hashlib
import argparse
import subprocess
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple, Optional

# Add scripts directory to sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from pdf_validator import validate_resume_pdf
    from db_manager import upsert_application, export_markdown_tracker, get_connection
except ImportError:
    pass

# Standard Edge installation path on Windows
DEFAULT_EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# Curated AI/ML & Engineering Skills Taxonomy for Fast Matching
TAXONOMY_KEYWORDS = {
    # Vision & Deep Learning
    "computer vision": "Computer Vision",
    "cv": "Computer Vision",
    "image processing": "Image Processing",
    "object detection": "Object Detection",
    "cascade r-cnn": "Cascade R-CNN",
    "rcnn": "R-CNN",
    "crnn": "CRNN",
    "ocr": "OCR",
    "trocr": "TrOCR",
    "handwritten": "Handwriting Recognition",
    "vision transformer": "Vision Transformers (ViT)",
    "vit": "Vision Transformers (ViT)",
    "retfound": "RETFound",
    "grad-cam": "Grad-CAM",
    "medical imaging": "Medical Imaging",
    "opencv": "OpenCV",
    "ctc loss": "CTC Loss",
    # GenAI & Agents
    "rag": "RAG Pipelines",
    "retrieval-augmented generation": "RAG Pipelines",
    "llm": "LLMs",
    "llms": "LLMs",
    "large language models": "LLMs",
    "generative ai": "Generative AI",
    "genai": "Generative AI",
    "agentic ai": "Agentic AI",
    "langchain": "LangChain",
    "langgraph": "LangGraph",
    "gemini": "Gemini API",
    "gemini api": "Gemini API",
    "prompt engineering": "Prompt Engineering",
    "sentence-transformers": "Sentence-Transformers",
    "embeddings": "Vector Embeddings",
    "vector search": "Vector Search",
    "faiss": "FAISS",
    "chromadb": "ChromaDB",
    "lora": "LoRA Fine-Tuning",
    "peft": "PEFT Fine-Tuning",
    "fine-tuning": "Model Fine-Tuning",
    "hugging face": "Hugging Face",
    "transformers": "Transformers",
    # Core ML & Frameworks
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "keras": "Keras",
    "scikit-learn": "scikit-learn",
    "deep learning": "Deep Learning",
    "machine learning": "Machine Learning",
    "transfer learning": "Transfer Learning",
    # Backend & Deployment
    "python": "Python",
    "fastapi": "FastAPI",
    "rest api": "REST APIs",
    "rest apis": "REST APIs",
    "restful": "REST APIs",
    "streamlit": "Streamlit",
    "docker": "Docker",
    "linux": "Linux",
    "modal": "Modal GPU",
    "gpu": "GPU Infrastructure",
    "sql": "SQL",
    "pandas": "Pandas",
    "git": "Git",
    # QA & Quality Automation
    "test automation": "Test Automation",
    "qa": "Quality Assurance",
    "tosca": "Tosca",
    "tosca vision ai": "Tosca Vision AI",
    "vision ai": "Tosca Vision AI",
    "qtest": "qTest",
    "salesforce": "Salesforce QA",
    "regression testing": "Regression Testing",
    "defect lifecycle": "Defect Lifecycle Management"
}

ARCHETYPE_MAP = {
    "vision": [
        "computer vision", "cv", "ocr", "trocr", "crnn", "cascade r-cnn", "vit",
        "vision transformer", "retfound", "grad-cam", "opencv", "medical imaging", "image processing"
    ],
    "rag": [
        "rag", "retrieval-augmented generation", "llm", "llms", "large language models",
        "generative ai", "genai", "agentic ai", "langchain", "langgraph", "gemini",
        "embeddings", "vector search", "faiss", "chromadb", "sentence-transformers"
    ],
    "backend": [
        "fastapi", "rest api", "docker", "linux", "modal", "microservices", "sql", "api", "backend"
    ],
    "qa": [
        "test automation", "qa", "tosca", "tosca vision ai", "qtest", "salesforce", "regression testing"
    ]
}

def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", text).strip("-_")

def load_canonical_profile(root_dir: Path) -> Dict[str, Any]:
    prof_path = root_dir / "data" / "canonical_profile.json"
    if not prof_path.exists():
        raise FileNotFoundError(f"Missing canonical profile at {prof_path}")
    with open(prof_path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_keywords_from_text(text: str) -> List[str]:
    """Fast regex-based tokenization against curated taxonomy."""
    text_lower = text.lower()
    matched = []
    for kw_raw, canonical in TAXONOMY_KEYWORDS.items():
        pattern = r"\b" + re.escape(kw_raw) + r"\b"
        if re.search(pattern, text_lower):
            if canonical not in matched:
                matched.append(canonical)
    return matched

def detect_archetype(jd_text: str, explicit_focus: Optional[str] = None) -> str:
    """Classifies the job archetype based on keyword frequencies."""
    if explicit_focus and explicit_focus.lower() in ("vision", "rag", "backend", "qa"):
        return explicit_focus.lower()

    text_lower = jd_text.lower()
    scores = {"vision": 0, "rag": 0, "backend": 0, "qa": 0}

    for arch, kws in ARCHETYPE_MAP.items():
        for kw in kws:
            pattern = r"\b" + re.escape(kw) + r"\b"
            matches = len(re.findall(pattern, text_lower))
            scores[arch] += matches

    # Default to vision or rag if tied or top
    best_arch = max(scores, key=scores.get)
    if scores[best_arch] == 0:
        return "vision"
    return best_arch

def score_ats_match(
    extracted_kws: List[str],
    candidate_skills: List[str]
) -> Tuple[float, List[str], List[str]]:
    """Calculates ATS keyword coverage, returning match % and diff sets."""
    candidate_kws_lower = {s.lower() for s in candidate_skills}
    
    matched = []
    missing = []
    
    for kw in extracted_kws:
        # Check if canonical name or part exists in candidate skills
        if any(kw.lower() in c or c in kw.lower() for c in candidate_kws_lower):
            matched.append(kw)
        else:
            missing.append(kw)
            
    total = len(extracted_kws)
    score_pct = (len(matched) / total * 100.0) if total > 0 else 85.0
    return round(score_pct, 1), matched, missing

def get_candidate_all_skills(profile: Dict[str, Any]) -> List[str]:
    skills = []
    taxonomy = profile.get("skills_taxonomy", {})
    for cat, items in taxonomy.items():
        skills.extend(items)

    # Also aggregate project tags
    for proj in profile.get("academic_and_research_projects", []):
        skills.extend(proj.get("tags", []))

    # Also aggregate coursework
    for ed in profile.get("education", []):
        skills.extend(ed.get("coursework", []))

    return list(set(skills))

def generate_tailored_headline(role: str, archetype: str) -> str:
    if archetype == "vision":
        return f"{role} | PyTorch, Vision Transformers, Cascade R-CNN & OCR"
    elif archetype == "rag":
        return f"{role} | GenAI, Semantic RAG, Sentence-Transformers & FastAPI"
    elif archetype == "qa":
        return f"{role} | Test Automation, Tosca Vision AI & Applied Machine Learning"
    else:
        return f"{role} | AI/ML Engineering, PyTorch, Deep Learning & Cloud Deployment"

def generate_tailored_summary(archetype: str, matched_kws: List[str]) -> str:
    highlight_skills = ", ".join(matched_kws[:6]) if matched_kws else "PyTorch, Computer Vision, and FastAPI"
    if archetype == "vision":
        return (
            f"AI & Machine Learning Engineer specialized in computer vision, vision-language foundation models, "
            f"and OCR architectures. Proven track record developing high-precision pipelines with {highlight_skills}, "
            f"achieving 97.5% detection accuracy with Cascade R-CNN and 94% medical classification with ViT foundation models. "
            f"Experienced deploying scalable inference services on GPU infrastructure with clean, production-grade Python."
        )
    elif archetype == "rag":
        return (
            f"AI & Machine Learning Engineer specialized in generative AI, semantic RAG systems, and production LLM integration. "
            f"Demonstrated success building end-to-end applications leveraging {highlight_skills}, including hybrid vector retrieval "
            f"(sentence-transformers, FAISS) and serverless GPU microservices on Modal and FastAPI. Grounded in rigorous "
            f"evaluation and clean software architecture."
        )
    elif archetype == "qa":
        return (
            f"Software Engineer combining 22 months of enterprise quality assurance and test automation experience at TCS "
            f"with advanced Master's training in AI/ML at KFUPM. Extensive hands-on background in {highlight_skills}, "
            f"automated regression testing with Tosca Vision AI, and building resilient Python backends."
        )
    else:
        return (
            f"Applied Machine Learning Engineer with strong capabilities across computer vision, generative AI, and backend microservices. "
            f"Experienced building production-ready AI systems with {highlight_skills}, evaluating foundation models, "
            f"and deploying robust REST APIs on containerized infrastructure."
        )

def build_skills_html(profile: Dict[str, Any], archetype: str, matched_kws: List[str]) -> str:
    taxonomy = profile.get("skills_taxonomy", {})
    matched_set = {k.lower() for k in matched_kws}

    # Ordering categories by archetype
    if archetype == "vision":
        order = ["ai_machine_learning", "genai_agentic", "software_backend", "tools_and_infra", "quality_and_automation"]
    elif archetype == "rag":
        order = ["genai_agentic", "ai_machine_learning", "software_backend", "tools_and_infra", "quality_and_automation"]
    elif archetype == "qa":
        order = ["quality_and_automation", "software_backend", "ai_machine_learning", "tools_and_infra", "genai_agentic"]
    else:
        order = ["ai_machine_learning", "software_backend", "genai_agentic", "tools_and_infra", "quality_and_automation"]

    category_labels = {
        "ai_machine_learning": "AI & Machine Learning",
        "genai_agentic": "Generative AI & LLMs",
        "software_backend": "Backend & Software",
        "quality_and_automation": "QA & Test Automation",
        "tools_and_infra": "Tools & Infrastructure"
    }

    rows = []
    for cat in order:
        items = taxonomy.get(cat, [])
        if not items:
            continue
        formatted_items = []
        for it in items:
            if it.lower() in matched_set:
                formatted_items.append(f"<strong>{it}</strong>")
            else:
                formatted_items.append(it)
        
        row_html = f"""
        <div class="skill-row">
          <div class="skill-label">{category_labels.get(cat, cat)}:</div>
          <div class="skill-values">{", ".join(formatted_items)}</div>
        </div>
        """
        rows.append(row_html.strip())

    return "\n".join(rows)

def build_projects_html(profile: Dict[str, Any], archetype: str, matched_kws: List[str]) -> str:
    projects = profile.get("academic_and_research_projects", [])
    
    # Prioritize project order based on archetype
    if archetype == "vision":
        proj_order = ["proj_arabic_ocr", "proj_reseeai", "proj_pre"]
    elif archetype == "rag":
        proj_order = ["proj_pre", "proj_arabic_ocr", "proj_reseeai"]
    else:
        proj_order = ["proj_arabic_ocr", "proj_pre", "proj_reseeai"]

    proj_map = {p["id"]: p for p in projects}
    sorted_projs = [proj_map[pid] for pid in proj_order if pid in proj_map]

    matched_set = {k.lower() for k in matched_kws}
    entries = []

    for proj in sorted_projs:
        title = proj["title"]
        inst = proj.get("institution", "KFUPM")
        years = proj.get("years", "2024 – 2026")
        url = proj.get("url", "")
        
        bullets_html = []
        for b in proj.get("verified_bullets", [])[:4]: # Select top 4 bullets
            # Bold matching keywords
            highlighted = b
            for kw in matched_kws:
                if len(kw) > 2 and kw.lower() in highlighted.lower():
                    # Case-insensitive wrap
                    pattern = re.compile(rf"\b({re.escape(kw)})\b", re.IGNORECASE)
                    highlighted = pattern.sub(r"<strong>\1</strong>", highlighted)
            bullets_html.append(f"<li>{highlighted}</li>")

        link_markup = f'<a class="entry-link" href="{url}" target="_blank">Project Link</a>' if url else ""

        entry_html = f"""
        <div class="entry">
          <div class="entry-header">
            <div>
              <span class="entry-title">{title}</span>
              <span class="entry-org"> — {inst}</span>
              {link_markup}
            </div>
            <div class="entry-date">{years}</div>
          </div>
          <ul class="bullets">
            {"".join(bullets_html)}
          </ul>
        </div>
        """
        entries.append(entry_html.strip())

    return "\n".join(entries)

def build_experience_html(profile: Dict[str, Any]) -> str:
    experiences = profile.get("professional_experience", [])
    entries = []

    # Display TCS and KFUPM GA with strict provenance
    for exp in experiences:
        role = exp.get("official_title", "")
        employer = exp.get("employer", "")
        loc = exp.get("location", "")
        s_date = exp.get("start_date", "")
        e_date = exp.get("end_date", "")
        
        bullets = exp.get("verified_bullets", [])[:3] # top 3
        bullets_html = "".join([f"<li>{b}</li>" for b in bullets])

        entry_html = f"""
        <div class="entry">
          <div class="entry-header">
            <div>
              <span class="entry-title">{role}</span>
              <span class="entry-org"> — {employer}</span>
            </div>
            <div class="entry-date">{s_date} – {e_date}</div>
          </div>
          <div class="entry-location">{loc}</div>
          <ul class="bullets">
            {bullets_html}
          </ul>
        </div>
        """
        entries.append(entry_html.strip())

    return "\n".join(entries)

def build_education_html(profile: Dict[str, Any]) -> str:
    ed_list = profile.get("education", [])
    entries = []
    for ed in ed_list:
        deg = ed.get("degree", "")
        major = ed.get("major", "")
        inst = ed.get("institution", "")
        loc = ed.get("location", "")
        s_date = ed.get("start_date", "")
        e_date = ed.get("end_date", "")
        gpa = ed.get("gpa", "")
        
        gpa_text = f" (GPA: {gpa})" if gpa else ""

        entry_html = f"""
        <div class="entry">
          <div class="entry-header">
            <div>
              <span class="entry-title">{deg} in {major}{gpa_text}</span>
              <span class="entry-org"> — {inst}</span>
            </div>
            <div class="entry-date">{s_date} – {e_date}</div>
          </div>
          <div class="entry-location">{loc}</div>
        </div>
        """
        entries.append(entry_html.strip())

    return "\n".join(entries)

def render_ats_html(
    profile: Dict[str, Any],
    company: str,
    role: str,
    archetype: str,
    matched_kws: List[str],
    template_path: Path
) -> str:
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    cand = profile.get("candidate", {})
    loc = cand.get("location", {})
    loc_str = f"{loc.get('city', 'Dhahran')}, {loc.get('country', 'Saudi Arabia')}"
    links = cand.get("links", {})

    replacements = {
        "{{CANDIDATE_NAME}}": cand.get("name", "Shabaaz Hussain Shaik"),
        "{{TAILORED_HEADLINE}}": generate_tailored_headline(role, archetype),
        "{{LOCATION}}": loc_str,
        "{{EMAIL}}": cand.get("email", "theshabaaz@outlook.com"),
        "{{PHONE}}": cand.get("phone", "+966 50 269 8140"),
        "{{LINKEDIN_URL}}": links.get("linkedin", "https://linkedin.com/in/redfries/"),
        "{{GITHUB_URL}}": links.get("github", "https://github.com/redfries"),
        "{{PORTFOLIO_URL}}": links.get("portfolio", "https://infinitys.me"),
        "{{TAILORED_SUMMARY}}": generate_tailored_summary(archetype, matched_kws),
        "{{SKILLS_ROWS}}": build_skills_html(profile, archetype, matched_kws),
        "{{PROJECTS_ENTRIES}}": build_projects_html(profile, archetype, matched_kws),
        "{{EXPERIENCE_ENTRIES}}": build_experience_html(profile),
        "{{EDUCATION_ENTRIES}}": build_education_html(profile)
    }

    for placeholder, val in replacements.items():
        template = template.replace(placeholder, val)

    return template

def compile_html_to_pdf_edge(html_path: Path, output_pdf_path: Path) -> float:
    """Invokes native Windows Edge headless to compile HTML to PDF."""
    t0 = time.time()
    edge_bin = shutil.which("msedge") or DEFAULT_EDGE_PATH
    if not Path(edge_bin).exists():
        raise FileNotFoundError(f"Microsoft Edge not found at {edge_bin}")

    cmd = [
        edge_bin,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={output_pdf_path.resolve()}",
        str(html_path.resolve())
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 or not output_pdf_path.exists():
        raise RuntimeError(f"Edge PDF render failed: {res.stderr}")

    duration = (time.time() - t0) * 1000.0
    return duration

def generate_block_h_screener_answers(
    profile: Dict[str, Any],
    company: str,
    role: str,
    archetype: str,
    matched_kws: List[str]
) -> Dict[str, str]:
    cand = profile.get("candidate", {})
    return {
        "technical_summary": (
            f"I have extensive hands-on experience in applied machine learning, computer vision, and backend systems. "
            f"My technical stack directly aligns with {company}'s requirements in {', '.join(matched_kws[:5])}. "
            f"At KFUPM, I engineered high-precision OCR models (Cascade R-CNN, CRNN) and RAG applications on GPU microservices. "
            f"Combined with 22 months of commercial test automation at TCS, I deliver reliable, production-tested AI solutions."
        ),
        "work_authorization": (
            "Authorized to work in Saudi Arabia (Resident on transferable KFUPM Iqama for employment). "
            "Indian citizen. Also eligible for Global Remote contractor / Deel engagements."
        ),
        "years_experience": "2+ years professional software/QA experience + 2 years academic AI research (Masters in AI at KFUPM).",
        "notice_period": "Immediate / Negotiable.",
        "portfolio_links": f"Portfolio: {cand['links']['portfolio']} | GitHub: {cand['links']['github']} | LinkedIn: {cand['links']['linkedin']}"
    }

def run_fast_tailor(
    company: str,
    role: str,
    jd_text: str,
    req_id: Optional[str] = None,
    source_url: Optional[str] = None,
    focus: Optional[str] = None,
    output_format: str = "ats",
    sync_to_notion_flag: bool = False,
    benchmark: bool = False
) -> Dict[str, Any]:
    t_start = time.time()
    timings = {}

    # 1. Ingestion & Extraction
    t0 = time.time()
    profile = load_canonical_profile(ROOT_DIR)
    candidate_skills = get_candidate_all_skills(profile)
    extracted_kws = extract_keywords_from_text(jd_text)
    archetype = detect_archetype(jd_text, explicit_focus=focus)
    ats_score, matched_kws, missing_kws = score_ats_match(extracted_kws, candidate_skills)
    timings["keyword_analysis_ms"] = (time.time() - t0) * 1000.0

    # 2. Bundle ID & Directory
    today = date.today().isoformat()
    company_slug = slugify(company)
    role_slug = slugify(role)
    app_id = f"{today}_{company_slug}_{role_slug}"
    if req_id:
        app_id += f"_{slugify(req_id)}"

    bundle_dir = ROOT_DIR / "applications" / app_id
    bundle_dir.mkdir(parents=True, exist_ok=True)

    # 3. HTML Generation
    t0 = time.time()
    template_path = ROOT_DIR / "templates" / "ats_resume_template.html"
    rendered_html = render_ats_html(
        profile=profile,
        company=company,
        role=role,
        archetype=archetype,
        matched_kws=matched_kws,
        template_path=template_path
    )
    html_file = bundle_dir / "resume.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    timings["html_render_ms"] = (time.time() - t0) * 1000.0

    # 4. PDF Compilation
    t0 = time.time()
    pdf_file = bundle_dir / "resume.pdf"
    render_time = compile_html_to_pdf_edge(html_file, pdf_file)
    timings["pdf_compile_ms"] = render_time

    # 5. Validation
    t0 = time.time()
    val_result = validate_resume_pdf(pdf_file, max_pages=2)
    timings["pdf_validation_ms"] = (time.time() - t0) * 1000.0

    if not val_result["valid"]:
        return {
            "success": False,
            "error": f"PDF validation failed: {val_result['errors']}",
            "timings": timings
        }

    # 6. Cryptographic Manifest
    manifest_data = {
        "application_id": app_id,
        "company": company,
        "role": role,
        "req_id": req_id,
        "archetype": archetype,
        "ats_match_percentage": ats_score,
        "matched_keywords": matched_kws,
        "missing_keywords": missing_kws,
        "build_date": datetime.now().isoformat(),
        "pdf_sha256": val_result["sha256"],
        "page_count": val_result["page_count"],
        "format": output_format,
        "renderer": "msedge_headless"
    }
    with open(bundle_dir / "submission_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    # 7. Database Registration
    t0 = time.time()
    holistic_score = min(5.0, max(1.0, round((ats_score / 20.0), 1)))
    try:
        upsert_application({
            "id": app_id,
            "company": company,
            "role": role,
            "req_id": req_id,
            "source_url": source_url,
            "status": "prepared",
            "folder_path": str(bundle_dir.resolve()),
            "pdf_sha256": val_result["sha256"],
            "holistic_score": holistic_score,
            "platform": "Direct",
            "notes": f"Fast ATS tailored: {archetype} focus. {ats_score}% keyword match."
        })
        tracker_file = ROOT_DIR / "job_research" / "active_application_tracker.md"
        export_markdown_tracker(tracker_file)
    except Exception as e:
        print(f"[Warning] SQLite upsert notice: {e}")
    timings["db_upsert_ms"] = (time.time() - t0) * 1000.0

    # 8. Screener Answers
    screener_answers = generate_block_h_screener_answers(
        profile=profile,
        company=company,
        role=role,
        archetype=archetype,
        matched_kws=matched_kws
    )
    with open(bundle_dir / "block_h_screener_answers.json", "w", encoding="utf-8") as f:
        json.dump(screener_answers, f, indent=2)

    total_time_ms = (time.time() - t_start) * 1000.0
    timings["total_execution_ms"] = total_time_ms

    # Optional Notion Sync
    if sync_to_notion_flag:
        try:
            from sync_to_notion import sync_applications_to_notion, load_env
            env = load_env(ROOT_DIR / ".env")
            if env.get("NOTION_API_KEY") and env.get("NOTION_DATABASE_ID"):
                sync_applications_to_notion(env["NOTION_API_KEY"], env["NOTION_DATABASE_ID"], root_dir=ROOT_DIR)
        except Exception as e:
            print(f"[Warning] Notion sync notice: {e}")

    return {
        "success": True,
        "application_id": app_id,
        "bundle_dir": str(bundle_dir),
        "pdf_path": str(pdf_file),
        "ats_score": ats_score,
        "archetype": archetype,
        "matched_keywords": matched_kws,
        "missing_keywords": missing_kws,
        "page_count": val_result["page_count"],
        "pdf_sha256": val_result["sha256"],
        "screener_answers": screener_answers,
        "timings": timings
    }

def main():
    parser = argparse.ArgumentParser(description="Sub-second ATS Resume Tailoring & Validation Engine")
    parser.add_argument("--company", required=True, help="Hiring company name")
    parser.add_argument("--role", required=True, help="Target role title")
    parser.add_argument("--jd", default=None, help="Raw Job Description text")
    parser.add_argument("--jd-file", default=None, help="Path to file containing Job Description")
    parser.add_argument("--req-id", default=None, help="Job requisition ID")
    parser.add_argument("--focus", choices=["vision", "rag", "backend", "qa", "auto"], default="auto", help="Archetype focus")
    parser.add_argument("--sync", action="store_true", help="Sync application to Notion immediately")
    parser.add_argument("--benchmark", action="store_true", help="Print detailed micro-benchmark timings")

    args = parser.parse_args()

    # Read JD
    jd_content = ""
    if args.jd:
        jd_content = args.jd
    elif args.jd_file:
        with open(args.jd_file, "r", encoding="utf-8") as f:
            jd_content = f.read()
    else:
        # Fallback to role name as JD signal
        jd_content = f"{args.role} at {args.company}"

    focus_val = None if args.focus == "auto" else args.focus

    res = run_fast_tailor(
        company=args.company,
        role=args.role,
        jd_text=jd_content,
        req_id=args.req_id,
        focus=focus_val,
        sync_to_notion_flag=args.sync,
        benchmark=args.benchmark
    )

    if not res["success"]:
        print(f"\n[Error] Tailoring failed: {res.get('error')}")
        sys.exit(1)

    print("\n" + "="*60)
    print(f"[SUCCESS] ATS RESUME TAILORED IN {res['timings']['total_execution_ms']:.1f}ms")
    print("="*60)
    print(f"Company:         {args.company}")
    print(f"Role:            {args.role}")
    print(f"Archetype:       {res['archetype'].upper()}")
    print(f"ATS Match Score: {res['ats_score']}%")
    print(f"Generated PDF:   {res['pdf_path']} ({res['page_count']} page)")
    print(f"SHA256 Checksum: {res['pdf_sha256'][:16]}...")
    
    print("\n--- [MATCH] Matched Keywords ---")
    if res["matched_keywords"]:
        print("  " + ", ".join(res["matched_keywords"]))
    else:
        print("  (Standard core AI/ML stack applied)")

    if res["missing_keywords"]:
        print("\n--- [MISSING] Missing / Nice-To-Have ---")
        print("  " + ", ".join(res["missing_keywords"]))

    if args.benchmark:
        print("\n--- [BENCHMARK] Micro-Timings ---")
        for stage, duration in res["timings"].items():
            print(f"  • {stage:<25}: {duration:.1f} ms")

    print("\n--- [SCREENER] Block H Answers (Ready for ATS Form) ---")
    for q_name, ans in res["screener_answers"].items():
        print(f"\n[{q_name.upper()}]:\n{ans}")
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
