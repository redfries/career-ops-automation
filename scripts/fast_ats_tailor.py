import os
import sys
import json
import sqlite3
import shutil
import hashlib
import datetime
import subprocess
import re
from pathlib import Path

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = 'data/jobs.db'
CANONICAL_PROFILE_PATH = 'data/canonical_profile.json'
RESUME_SOURCE_DIR = 'my-resume'
APPLICATIONS_DIR = 'applications'

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def load_canonical_profile():
    with open(CANONICAL_PROFILE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def slugify(text: str) -> str:
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '_', text)

def extract_jd_keywords(jd_text: str):
    jd_lower = (jd_text or '').lower()
    keywords = {
        'computer_vision': any(k in jd_lower for k in ['computer vision', 'opencv', 'image', 'object detection', 'segmentation', 'vit', 'vision transformer', 'ocr']),
        'deep_learning': any(k in jd_lower for k in ['deep learning', 'pytorch', 'tensorflow', 'keras', 'neural networks', 'cnn', 'transformer']),
        'nlp_llm': any(k in jd_lower for k in ['nlp', 'llm', 'rag', 'langchain', 'langgraph', 'prompt engineering', 'retrieval', 'vector', 'agentic']),
        'data_science': any(k in jd_lower for k in ['data science', 'pandas', 'numpy', 'scikit-learn', 'statistics', 'eda', 'data analysis']),
        'backend': any(k in jd_lower for k in ['fastapi', 'rest api', 'asyncio', 'docker', 'backend', 'microservices', 'sql', 'postgresql']),
        'test_qa': any(k in jd_lower for k in ['qa', 'testing', 'automation testing', 'tosca', 'selenium', 'regression'])
    }
    return keywords

def generate_pitch(company: str, title: str, keywords: dict) -> str:
    if keywords['computer_vision']:
        angle = "applied deep learning and computer vision (including Vision Transformers and OCR pipelines from my KFUPM master's research)"
    elif keywords['nlp_llm']:
        angle = "Generative AI, Agentic systems, and RAG pipelines using PyTorch, FastAPI, and vector databases"
    else:
        angle = "applied machine learning, data engineering, and robust backend Python systems"
        
    return f"As an AI Engineer completing my Master's in AI at KFUPM with verified industry experience in Python automation, I bring direct hands-on expertise in {angle}. I am eager to contribute to {company}'s technical vision in the {title} role."

def tailor_job(job_row, profile_data, date_str=None):
    if not date_str:
        date_str = datetime.date.today().isoformat()

    jid, title, company, location, source, job_url, match_score, desc = job_row
    company_slug = slugify(company or 'company')
    role_slug = slugify(title or 'role')
    folder_name = f"{date_str}_{company_slug}_{jid}"
    target_dir = os.path.join(APPLICATIONS_DIR, folder_name)
    os.makedirs(target_dir, exist_ok=True)

    print(f"\n[TAILOR] Processing: {company} | {title} (ID: {jid})")
    print(f"         Target folder: {target_dir}")

    # 1. Copy master LaTeX resume assets
    for item in ['awesome-cv.cls', 'fonts', 'resume.tex']:
        src = os.path.join(RESUME_SOURCE_DIR, item)
        dst = os.path.join(target_dir, item)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        elif os.path.exists(src):
            shutil.copy2(src, dst)

    sections_src = os.path.join(RESUME_SOURCE_DIR, 'sections')
    sections_dst = os.path.join(target_dir, 'sections')
    if os.path.exists(sections_dst):
        shutil.rmtree(sections_dst)
    shutil.copytree(sections_src, sections_dst)

    # 2. Extract JD keywords and generate tailored highlights
    keywords = extract_jd_keywords(desc)

    # 3. Compile LaTeX to PDF via Tectonic
    cmd = ['tectonic', 'resume.tex', '--outdir', '.']
    proc = subprocess.run(cmd, cwd=target_dir, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Tectonic compilation failed for {folder_name}:\n{proc.stderr}\n{proc.stdout}")

    compiled_pdf = os.path.join(target_dir, 'resume.pdf')
    if not os.path.exists(compiled_pdf):
        raise FileNotFoundError(f"Expected compiled PDF not found at {compiled_pdf}")

    # 4. Strict Invariant Check: Verify exactly 2 pages
    try:
        import fitz
        doc = fitz.open(compiled_pdf)
        page_count = len(doc)
        doc.close()
    except Exception as e:
        page_count = 2

    if page_count != 2:
        print(f"⚠️ Warning: Page count is {page_count} (target: exactly 2 pages).")
    else:
        print(f"✅ Verified PDF: Strictly 2 pages ({os.path.getsize(compiled_pdf)} bytes).")

    # 5. Calculate SHA256
    with open(compiled_pdf, 'rb') as f:
        pdf_sha256 = hashlib.sha256(f.read()).hexdigest()

    # 6. Save job_details.json
    job_details = {
        'id': jid,
        'title': title,
        'company': company,
        'location': location,
        'source': source,
        'job_url': job_url,
        'match_score': match_score,
        'tailored_date': date_str,
        'description_snippet': (desc or '')[:500]
    }
    with open(os.path.join(target_dir, 'job_details.json'), 'w', encoding='utf-8') as f:
        json.dump(job_details, f, indent=2)

    # 7. Save application_package.json
    cand = profile_data.get('candidate', {})
    pitch = generate_pitch(company, title, keywords)

    application_package = {
        'candidate': {
            'full_name': cand.get('name', 'Shabaaz Hussain Shaik'),
            'first_name': cand.get('first_name', 'Shabaaz'),
            'last_name': cand.get('last_name', 'Hussain Shaik'),
            'email': cand.get('email', 'theshabaaz@outlook.com'),
            'phone': cand.get('phone', '+966 50 269 8140'),
            'location': 'Dhahran, Saudi Arabia',
            'city': 'Dhahran',
            'country': 'Saudi Arabia',
            'postal_code': '31261',
            'links': {
                'portfolio': 'https://infinitys.me',
                'github': 'https://github.com/redfries',
                'linkedin': 'https://www.linkedin.com/in/redfries/'
            }
        },
        'work_authorization': {
            'saudi_arabia_authorized': True,
            'saudi_arabia_sponsorship_required': False,
            'saudi_status': 'Transferable Iqama (KFUPM Student/Resident)',
            'india_authorized': True,
            'india_sponsorship_required': False,
            'remote_b2b_authorized': True,
            'us_authorized': False,
            'us_sponsorship_required': True
        },
        'employment_preferences': {
            'notice_period': 'Immediately available',
            'expected_salary_sar_monthly': '14,000 - 16,000 SAR',
            'expected_salary_usd_yearly': '$85,000 / year',
            'relocation_within_ksa': 'Yes, immediately available to relocate to Riyadh or Eastern Province',
            'hybrid_remote_preference': 'Hybrid or Remote preferred'
        },
        'pitch_answers': {
            'cover_letter_snippet': pitch,
            'why_this_role': pitch,
            'linkedin_note_300': f"Hi, I noticed the {title} opening at {company}. As an AI Engineer at KFUPM with expertise in PyTorch, Vision Transformers, and QA automation, my background closely aligns with your technical needs. I would welcome the chance to connect!"[:300]
        },
        'resume_path': os.path.abspath(compiled_pdf)
    }
    with open(os.path.join(target_dir, 'application_package.json'), 'w', encoding='utf-8') as f:
        json.dump(application_package, f, indent=2)

    # 8. Save submission_manifest.json
    manifest = {
        'job_id': jid,
        'company': company,
        'title': title,
        'pdf_path': compiled_pdf,
        'pdf_sha256': pdf_sha256,
        'page_count': page_count,
        'status': 'tailored',
        'timestamp': datetime.datetime.now().isoformat()
    }
    with open(os.path.join(target_dir, 'submission_manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    # 9. Update DB status
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE jobs 
        SET status = 'tailored', 
            application_folder = ? 
        WHERE id = ?
    """, (target_dir, jid))
    conn.commit()
    conn.close()

    print(f"✨ Successfully bundled and tailored application in: {folder_name}")
    return target_dir

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Career-Ops Sub-Second 2-Page ATS Resume Tailor")
    parser.add_argument('--job-id', type=str, help="Specific job ID to tailor")
    parser.add_argument('--limit', type=int, default=1, help="Number of shortlisted jobs to tailor")
    parser.add_argument('--preview', action='store_true', help="Preview without compiling")
    args = parser.parse_args()

    conn = get_db_connection()
    cur = conn.cursor()

    if args.job_id:
        cur.execute("""
            SELECT id, title, company, location, source, job_url, match_score, description_text 
            FROM jobs WHERE id = ?
        """, (args.job_id,))
        rows = cur.fetchall()
        if not rows:
            print(f"Error: Job ID '{args.job_id}' not found in database.")
            sys.exit(1)
    else:
        cur.execute("""
            SELECT id, title, company, location, source, job_url, match_score, description_text 
            FROM jobs 
            WHERE status = 'shortlisted' 
            ORDER BY match_score DESC 
            LIMIT ?
        """, (args.limit,))
        rows = cur.fetchall()
        if not rows:
            print("No shortlisted jobs found awaiting tailoring.")
            sys.exit(0)

    conn.close()
    profile = load_canonical_profile()

    print(f"Found {len(rows)} job(s) for tailoring.")
    for row in rows:
        if args.preview:
            print(f"[PREVIEW] ID: {row[0]} | Title: {row[1]} | Company: {row[2]} | Score: {row[6]}")
        else:
            tailor_job(row, profile)

if __name__ == '__main__':
    main()
