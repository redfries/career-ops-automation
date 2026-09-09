#!/usr/bin/env python3
"""
compile_tailored_resume.py
Collision-proof, validated LaTeX resume compiler:
1. Stable, collision-proof folder naming: applications/<YYYY-MM-DD>_<company_slug>_<role_slug>_<req_or_short_id>/
2. Safe LaTeX special character escaping (&, %, $, #, _, etc.)
3. Substantive tailoring of summary, skills, and project ordering based on canonical evidence
4. Isolated staging compilation via Tectonic XeTeX
5. Multi-step post-compilation PDF validation (header, size, text streams, page count)
6. Cryptographic manifest recording (SHA256, build timestamp, review status)
"""

import os
import sys
import re
import json
import shutil
import hashlib
import argparse
import subprocess
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Import PDF validator from same directory
try:
    from pdf_validator import validate_resume_pdf
except ImportError:
    from scripts.pdf_validator import validate_resume_pdf

def slugify(text: str) -> str:
    """Converts string into a safe, clean lowercase slug."""
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", text).strip("-_")

def escape_latex_text(text: str) -> str:
    """Escapes special LaTeX characters in plain text while preserving existing backslashed commands."""
    # If the text is raw text from user or config, escape problematic LaTeX chars:
    # & % $ # _ { } ~ ^
    replacements = [
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
    ]
    for char, escaped in replacements:
        # Don't double-escape if already preceded by backslash
        pattern = r"(?<!\\)" + re.escape(char)
        text = re.sub(pattern, escaped, text)
    return text

def load_canonical_profile(root_dir: Path) -> Dict[str, Any]:
    prof_path = root_dir / "data" / "canonical_profile.json"
    if not prof_path.exists():
        raise FileNotFoundError(f"Canonical profile missing at {prof_path}")
    with open(prof_path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_tailored_summary(role: str, focus: str) -> str:
    """Generates tailored About Me cvparagraph using only verified facts."""
    focus_lower = (focus or "").lower()
    role_lower = (role or "").lower()
    
    if "vision" in focus_lower or "ocr" in focus_lower or "vision" in role_lower:
        emphasis = "Specialized in computer vision systems (Cascade R-CNN, ViT foundation models, CRNN) and fine-tuning vision-language models, with a proven track record delivering 97.5% detection accuracy and 94% medical classification."
    elif "rag" in focus_lower or "agent" in focus_lower or "llm" in focus_lower:
        emphasis = "Specialized in generative AI, semantic RAG pipelines (sentence-transformers, vector embeddings), and production LLM integration via FastAPI and Modal GPU infrastructure."
    elif "qa" in focus_lower or "test" in focus_lower or "automation" in role_lower:
        emphasis = "Extensive experience combining software quality engineering and test automation with applied machine learning and data engineering pipelines."
    else:
        emphasis = "Focused on developing computer vision systems, fine-tuning foundation models, and building practical full-stack AI applications with robust backend deployment."

    return (
        "%-------------------------------------------------------------------------------\n"
        "%	SECTION TITLE\n"
        "%-------------------------------------------------------------------------------\n"
        "\\cvsection{About Me}\n\n\n"
        "%-------------------------------------------------------------------------------\n"
        "%	CONTENT\n"
        "%-------------------------------------------------------------------------------\n"
        "\\begin{cvparagraph}\n\n"
        f"AI and Machine Learning Engineer currently pursuing a Master's in AI at KFUPM with prior software industry experience. {emphasis}\n\n"
        "\\end{cvparagraph}\n"
    )

def generate_tailored_skills(focus: str, canonical: Dict[str, Any]) -> str:
    """Renders skills.tex with strategic ordering based on job focus."""
    skills_tax = canonical.get("skills_taxonomy", {})
    ai_skills = ", ".join(skills_tax.get("ai_machine_learning", []))
    genai_skills = ", ".join(skills_tax.get("genai_agentic", []))
    backend_skills = ", ".join(skills_tax.get("software_backend", []))
    tools_skills = ", ".join(skills_tax.get("tools_and_infra", []))
    lang_skills = ", ".join(skills_tax.get("spoken_languages", []))

    # Determine ordering
    focus_lower = (focus or "").lower()
    if "rag" in focus_lower or "agent" in focus_lower:
        ordered_skills = [
            ("GenAI \\& Agentic Systems", genai_skills),
            ("AI / Machine Learning", ai_skills),
            ("Software \\& Backend", backend_skills),
            ("Tools \\& Infrastructure", tools_skills),
            ("Languages", lang_skills)
        ]
    else:
        ordered_skills = [
            ("AI / Machine Learning", ai_skills),
            ("GenAI \\& Agentic Systems", genai_skills),
            ("Software \\& Backend", backend_skills),
            ("Tools \\& Infrastructure", tools_skills),
            ("Languages", lang_skills)
        ]

    content = [
        "%-------------------------------------------------------------------------------",
        "%	SECTION TITLE",
        "%-------------------------------------------------------------------------------",
        "\\cvsection{Skills}\n\n",
        "%-------------------------------------------------------------------------------",
        "%	CONTENT",
        "%-------------------------------------------------------------------------------",
        "\\begin{cvskills}\n"
    ]

    for title, items in ordered_skills:
        safe_items = escape_latex_text(items)
        content.append("  \\cvskill")
        content.append(f"    {{{title}}}")
        content.append(f"    {{{safe_items}}}\n")

    content.append("\\end{cvskills}\n")
    return "\n".join(content)

def reorder_projects_for_role(focus: str, canonical: Dict[str, Any]) -> str:
    """Generates projects.tex with the most relevant KFUPM research project listed first."""
    projects = canonical.get("academic_and_research_projects", [])
    focus_lower = (focus or "").lower()

    # Determine priority order
    if "vision" in focus_lower or "ocr" in focus_lower or "image" in focus_lower:
        order = ["proj_arabic_ocr", "proj_reseeai", "proj_pre"]
    elif "rag" in focus_lower or "llm" in focus_lower or "nlp" in focus_lower:
        order = ["proj_pre", "proj_arabic_ocr", "proj_reseeai"]
    elif "medical" in focus_lower or "health" in focus_lower:
        order = ["proj_reseeai", "proj_arabic_ocr", "proj_pre"]
    else:
        order = ["proj_pre", "proj_arabic_ocr", "proj_reseeai"]

    proj_map = {p["id"]: p for p in projects}
    sorted_projs = [proj_map[pid] for pid in order if pid in proj_map]

    lines = [
        "%-------------------------------------------------------------------------------",
        "%	SECTION TITLE",
        "%-------------------------------------------------------------------------------",
        "\\cvsection{Projects}\n\n",
        "%-------------------------------------------------------------------------------",
        "%	CONTENT",
        "%-------------------------------------------------------------------------------",
        "\\begin{cventries}\n"
    ]

    for p in sorted_projs:
        p_type = escape_latex_text(f"{p['type']} · {p['institution']}")
        p_title = escape_latex_text(p["title"])
        raw_url = p.get("url", "")
        display_url = raw_url.replace("https://", "").replace("http://", "")
        p_link = f"\\href{{{raw_url}}}{{{display_url}}}"
        p_years = escape_latex_text(p.get("years", ""))

        lines.append("  \\cventry")
        lines.append(f"    {{{p_type}}}")
        lines.append(f"    {{{p_title}}}")
        lines.append(f"    {{{p_link}}}")
        lines.append(f"    {{{p_years}}}")
        lines.append("    {")
        lines.append("      \\begin{cvitems}")
        for bullet in p.get("verified_bullets", []):
            safe_bullet = escape_latex_text(bullet)
            lines.append(f"        \\item {{{safe_bullet}}}")
        lines.append("      \\end{cvitems}")
        lines.append("    }\n")

    lines.append("\\end{cventries}\n")
    return "\n".join(lines)

def compile_pdf_in_dir(working_dir: Path) -> subprocess.CompletedProcess:
    """Executes tectonic XeTeX on resume.tex in target directory."""
    tectonic_path = shutil.which("tectonic")
    if not tectonic_path:
        local_py_tectonic = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python" / "Python312" / "Scripts" / "tectonic.exe"
        if local_py_tectonic.exists():
            tectonic_path = str(local_py_tectonic)

    if not tectonic_path:
        raise FileNotFoundError("tectonic.exe compiler not found on PATH or Python Scripts folder.")

    cmd = [tectonic_path, "resume.tex"]
    return subprocess.run(cmd, cwd=working_dir, capture_output=True, text=True)

def build_application_bundle(
    company: str,
    role: str,
    target_date: Optional[str] = None,
    req_id: Optional[str] = None,
    focus: Optional[str] = None,
    source_url: Optional[str] = None,
    jd_text: Optional[str] = None,
    eval_text: Optional[str] = None,
    screener_answers: Optional[Dict[str, str]] = None,
    root_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main compilation and packaging routine:
    1. Sets up collision-proof identifier
    2. Stages and tailors LaTeX in temporary workspace
    3. Compiles via Tectonic
    4. Validates output PDF
    5. Publishes to final folder and writes submission_manifest.json
    """
    if not root_dir:
        root_dir = Path(__file__).resolve().parent.parent

    target_date = target_date or str(date.today())
    canonical = load_canonical_profile(root_dir)

    company_slug = slugify(company) or "company"
    role_slug = slugify(role) or "role"
    
    # Deterministic unique suffix from req_id or short hash
    if req_id:
        unique_suffix = slugify(req_id)[:16]
    else:
        hash_input = f"{company}_{role}_{target_date}_{source_url or ''}"
        unique_suffix = hashlib.md5(hash_input.encode("utf-8")).hexdigest()[:8]

    app_id = f"{target_date}_{company_slug}_{role_slug}_{unique_suffix}"
    final_dir = root_dir / "applications" / app_id
    staging_dir = root_dir / "applications" / f".staging_{app_id}"

    # Clean staging directory
    if staging_dir.exists():
        shutil.rmtree(staging_dir, ignore_errors=True)
    staging_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Copy master template assets
        template_dir = root_dir / "my-resume"
        shutil.copy2(template_dir / "awesome-cv.cls", staging_dir / "awesome-cv.cls")
        shutil.copytree(template_dir / "fonts", staging_dir / "fonts", dirs_exist_ok=True)
        shutil.copytree(template_dir / "sections", staging_dir / "sections", dirs_exist_ok=True)

        # Read base resume.tex
        with open(template_dir / "resume.tex", "r", encoding="utf-8") as f:
            base_tex = f.read()

        # Update \position in resume.tex
        safe_role = escape_latex_text(role)
        tailored_tex = re.sub(
            r"\\position\{[^\r\n]+\}",
            lambda m: f"\\position{{{safe_role}}}",
            base_tex
        )
        with open(staging_dir / "resume.tex", "w", encoding="utf-8") as f:
            f.write(tailored_tex)

        # Tailor sections/about-me.tex
        summary_content = generate_tailored_summary(role, focus or role)
        with open(staging_dir / "sections" / "about-me.tex", "w", encoding="utf-8") as f:
            f.write(summary_content)

        # Tailor sections/skills.tex
        skills_content = generate_tailored_skills(focus or role, canonical)
        with open(staging_dir / "sections" / "skills.tex", "w", encoding="utf-8") as f:
            f.write(skills_content)

        # Reorder sections/projects.tex
        projects_content = reorder_projects_for_role(focus or role, canonical)
        with open(staging_dir / "sections" / "projects.tex", "w", encoding="utf-8") as f:
            f.write(projects_content)

        # Compile in staging
        compile_res = compile_pdf_in_dir(staging_dir)
        staged_pdf = staging_dir / "resume.pdf"

        if compile_res.returncode != 0 or not staged_pdf.exists():
            return {
                "success": False,
                "application_id": app_id,
                "error": f"LaTeX compilation failed: {compile_res.stderr or compile_res.stdout}"
            }

        # Validate staged PDF
        val_result = validate_resume_pdf(staged_pdf, max_pages=2)
        if not val_result["valid"]:
            return {
                "success": False,
                "application_id": app_id,
                "error": f"PDF validation failed: {val_result['errors']}",
                "validation_details": val_result
            }

        # Promotion: Atomically publish staging to final destination
        final_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(staging_dir, final_dir, dirs_exist_ok=True)

        # Write Job Description markdown
        jd_file = final_dir / "job_description.md"
        with open(jd_file, "w", encoding="utf-8") as f:
            f.write(f"# Job Description: {role} at {company}\n\n")
            f.write(f"- **Source URL**: {source_url or 'N/A'}\n")
            f.write(f"- **Captured Date**: {target_date}\n\n")
            f.write(jd_text or "No raw job description provided.\n")

        # Write Evaluation Report markdown
        eval_file = final_dir / "evaluation_report.md"
        with open(eval_file, "w", encoding="utf-8") as f:
            f.write(f"# Career-Ops Evaluation Report: {company} - {role}\n\n")
            f.write(eval_text or "Evaluation pending or conducted via db_manager.\n")

        # Write Screener Answers markdown
        screener_file = final_dir / "screener_answers.md"
        with open(screener_file, "w", encoding="utf-8") as f:
            f.write(f"# Custom Screener Answers: {company}\n\n")
            if screener_answers:
                for q, a in screener_answers.items():
                    f.write(f"### Question:\n{q}\n\n**Tailored Answer**:\n{a}\n\n---\n\n")
            else:
                f.write("No custom screening questions recorded.\n")

        # Write Cryptographic Submission Manifest
        manifest_data = {
            "application_id": app_id,
            "folder_name": app_id,
            "company": company,
            "role": role,
            "req_id": req_id or unique_suffix,
            "source_url": source_url,
            "canonical_url": source_url,
            "pdf_sha256": val_result["sha256"],
            "pdf_size_bytes": val_result["size_bytes"],
            "page_count": val_result["page_count"],
            "build_timestamp": datetime.now().isoformat(),
            "status": "prepared",
            "review_approved": False,
            "submission_evidence": None
        }

        manifest_file = final_dir / "submission_manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        return {
            "success": True,
            "application_id": app_id,
            "final_directory": str(final_dir),
            "pdf_path": str(final_dir / "resume.pdf"),
            "pdf_sha256": val_result["sha256"],
            "page_count": val_result["page_count"],
            "manifest": manifest_data
        }

    finally:
        # Cleanup staging
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)

def main():
    parser = argparse.ArgumentParser(description="Compile collision-proof tailored resume and generate manifest.")
    parser.add_argument("--company", required=True, help="Target company name")
    parser.add_argument("--role", required=True, help="Target role title")
    parser.add_argument("--req-id", default=None, help="Requisition or job post ID")
    parser.add_argument("--date", default=None, help="Date YYYY-MM-DD")
    parser.add_argument("--focus", default=None, help="Domain focus: 'vision', 'rag', 'backend', 'qa'")
    parser.add_argument("--url", default=None, help="Job posting URL")

    args = parser.parse_args()
    res = build_application_bundle(
        company=args.company,
        role=args.role,
        target_date=args.date,
        req_id=args.req_id,
        focus=args.focus,
        source_url=args.url
    )

    if res["success"]:
        print(f"\n[Success] Application bundle created: {res['application_id']}")
        print(f" -> Directory: {res['final_directory']}")
        print(f" -> PDF SHA256: {res['pdf_sha256']}")
        print(f" -> Page Count: {res['page_count']}")
    else:
        print(f"\n[Error] Failed to build application bundle: {res.get('error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
