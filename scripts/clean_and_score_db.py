import sqlite3
import json
import re
import hashlib
import sys
import os

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = 'data/jobs.db'
FRESH_LINKEDIN_PATH = 'data/fresh_linkedin_jobs.json'

def clean_and_score():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("==================================================")
    print("STEP 1: PURGE CORRUPT NAUKRI RECORDS (0 DESCRIPTIONS / PARSER NOISE)")
    print("==================================================")
    cur.execute("SELECT count(*) FROM jobs WHERE source = 'naukri'")
    naukri_count = cur.fetchone()[0]
    cur.execute("DELETE FROM jobs WHERE source = 'naukri'")
    conn.commit()
    print(f"Purged {naukri_count} broken/noisy Naukrigulf rows.")

    print("\n==================================================")
    print("STEP 2: BACKFILL 112 MISSING LINKEDIN JOBS")
    print("==================================================")
    if os.path.exists(FRESH_LINKEDIN_PATH):
        with open(FRESH_LINKEDIN_PATH, 'r', encoding='utf-8') as f:
            fresh_jobs = json.load(f)

        cur.execute("SELECT id FROM jobs WHERE id IS NOT NULL")
        existing_ids = set(r[0] for r in cur.fetchall())

        inserted_linkedin = 0
        for item in fresh_jobs:
            job_id = str(item.get('id', '') or '')
            if not job_id or job_id in existing_ids:
                continue

            title = (item.get('title') or '').strip()
            company = (item.get('companyName') or '').strip()
            if not title or not company:
                continue

            location = item.get('location', '')
            job_url = item.get('link', '') or item.get('url', '')
            posted_date = item.get('postedAt', '')
            applicants = item.get('applicantsCount', '')
            seniority = item.get('seniorityLevel', '')
            emp_type = item.get('employmentType', '')
            industries = item.get('industries', '')
            desc = (item.get('descriptionText') or '').strip()
            comp_web = item.get('companyWebsite', '')
            comp_desc = item.get('companyDescription', '')

            try:
                cur.execute('''
                    INSERT INTO jobs (
                        id, title, company, location, source, job_url, posted_date,
                        applicants_count, seniority_level, employment_type,
                        industries, description_text, company_website, company_description,
                        status
                    ) VALUES (?, ?, ?, ?, 'linkedin', ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')
                ''', (
                    job_id, title, company, location, job_url, posted_date,
                    applicants, seniority, emp_type, industries, desc, comp_web, comp_desc
                ))
                existing_ids.add(job_id)
                inserted_linkedin += 1
            except sqlite3.IntegrityError:
                pass

        conn.commit()
        print(f"Successfully inserted {inserted_linkedin} previously missing LinkedIn jobs.")
    else:
        print(f"Warning: {FRESH_LINKEDIN_PATH} not found.")

    print("\n==================================================")
    print("STEP 3: ASSIGN DETERMINISTIC IDS & CLEAN BAYT / INDEED")
    print("==================================================")
    cur.execute("SELECT rowid, source, job_url, company, title FROM jobs WHERE id IS NULL OR id = ''")
    rows_to_id = cur.fetchall()
    print(f"Found {len(rows_to_id)} rows missing unique ID.")

    updated_ids = 0
    for rowid, source, url, company, title in rows_to_id:
        url_str = url or ''
        # Try extracting job ID from URL
        extracted_id = None
        if source == 'bayt':
            # e.g. https://www.bayt.com/en/saudi-arabia/jobs/...-74977715/
            m = re.search(r'-(\d{7,10})(?:/|\?|$)', url_str)
            if m:
                extracted_id = f"bayt_{m.group(1)}"
        elif source == 'indeed':
            # e.g. jk=1a2b3c4d5e
            m = re.search(r'jk=([a-zA-Z0-9]+)', url_str)
            if m:
                extracted_id = f"indeed_{m.group(1)}"

        if not extracted_id:
            raw_hash = hashlib.md5(f"{source}_{company}_{title}_{url_str}".encode('utf-8')).hexdigest()[:12]
            extracted_id = f"{source}_{raw_hash}"

        cur.execute("UPDATE jobs SET id = ? WHERE rowid = ?", (extracted_id, rowid))
        updated_ids += 1

    conn.commit()
    print(f"Assigned deterministic unique IDs to {updated_ids} rows.")

    print("\n==================================================")
    print("STEP 4: GEOGRAPHIC CLASSIFICATION & WORK AUTH TAGGING")
    print("==================================================")
    cur.execute("SELECT id, title, company, location, description_text FROM jobs")
    all_jobs = cur.fetchall()

    tagged_us = 0
    saudi_count = 0
    uae_count = 0
    remote_count = 0
    other_count = 0

    us_states = [
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
    ]
    state_pattern = re.compile(r',\s*(' + '|'.join(us_states) + r')(?:\s|$|,)', re.IGNORECASE)
    us_keywords = [
        'united states', 'usa', 'san jose', 'seattle', 'san francisco', 'bay area',
        'austin', 'boston', 'los angeles', 'new york', 'sunnyvale', 'mountain view',
        'palo alto', 'redmond', 'chicago', 'manhattan', 'brooklyn'
    ]

    for jid, title, comp, loc, desc in all_jobs:
        # Clean markdown artifacts from location and company
        cleaned_loc = loc or ''
        cleaned_comp = comp or ''
        
        # Remove markdown images: ![...](...)
        cleaned_loc = re.sub(r'!\[.*?\]\(.*?\)', '', cleaned_loc).strip()
        cleaned_comp = re.sub(r'!\[.*?\]\(.*?\)', '', cleaned_comp).strip()
        
        # Clean <br> artifacts in location (e.g. "Infosys<br>Al Khobar |")
        if '<br>' in cleaned_loc:
            parts = [p.strip() for p in cleaned_loc.split('<br>') if p.strip()]
            if parts:
                cleaned_loc = parts[-1]  # The actual location is typically the last part
        
        # Clean trailing pipes or spaces
        cleaned_loc = cleaned_loc.rstrip(' |').strip()
        
        # Update cleaned location and company back to DB
        if cleaned_loc != loc or cleaned_comp != comp:
            cur.execute("UPDATE jobs SET location = ?, company = ? WHERE id = ?", (cleaned_loc, cleaned_comp, jid))

        loc_lower = cleaned_loc.lower()
        title_lower = (title or '').lower()

        # Check Saudi
        if any(k in loc_lower for k in ['saudi', 'riyadh', 'jeddah', 'dammam', 'khobar', 'dhahran', 'mecca', 'medina', 'jubail', 'yanbu', 'ksa', 'makkah']):
            geo = 'Saudi Arabia'
            saudi_count += 1
        elif any(k in loc_lower for k in ['uae', 'dubai', 'abu dhabi', 'sharjah', 'united arab emirates', 'ajman', 'ras al khaimah']):
            geo = 'UAE'
            uae_count += 1
        elif 'remote' in loc_lower or 'remote' in title_lower:
            geo = 'Remote'
            remote_count += 1
        elif any(k in loc_lower for k in us_keywords) or state_pattern.search(cleaned_loc):
            geo = 'United States'
            tagged_us += 1
        else:
            geo = 'Other'
            other_count += 1

        # Tag US jobs as out_of_region since candidate lacks US work visa
        if geo == 'United States':
            cur.execute("""
                UPDATE jobs 
                SET status = 'out_of_region', 
                    notes = 'US Location - Candidate has no US work authorization (requires H-1B/O-1)'
                WHERE id = ?
            """, (jid,))
        else:
            cur.execute("UPDATE jobs SET notes = NULL WHERE id = ?", (jid,))

    conn.commit()
    print(f"Region Classification:")
    print(f"  - Saudi Arabia (Direct Resident / Iqama Transfer): {saudi_count}")
    print(f"  - UAE (GCC Neighbor / Sponsorship Eligible): {uae_count}")
    print(f"  - Remote (Global / Contractor): {remote_count}")
    print(f"  - United States (Tagged out_of_region): {tagged_us}")
    print(f"  - Other / Unclassified: {other_count}")

    print("\n==================================================")
    print("STEP 5: CAREER-OPS MATCH SCORING (CRITERIA A - H)")
    print("==================================================")
    # Candidate Profile: Shabaaz Hussain Shaik
    # MS in AI (KFUPM), PyTorch, Computer Vision (Retinal ViT, Arabic OCR), NLP/LLMs, RAG, FastAPI, Modal GPU, Docker, SQL
    # Transferable Iqama in KSA (Highest Priority), UAE Sponsorship (High Priority)
    # Avoid: QA/Test Engineer, pure frontend, senior roles (7+ yrs)

    cur.execute("SELECT id, title, company, location, seniority_level, description_text, status FROM jobs")
    jobs_to_score = cur.fetchall()

    shortlisted_count = 0
    evaluated_count = 0
    low_fit_count = 0

    for jid, title, comp, loc, seniority, desc, current_status in jobs_to_score:
        if current_status == 'out_of_region':
            # Skip or keep score lower for out of region
            cur.execute("UPDATE jobs SET match_score = 0 WHERE id = ?", (jid,))
            continue

        text_corpus = f"{title} {comp} {desc}".lower()
        title_lower = (title or '').lower()
        sen_lower = (seniority or '').lower()
        loc_lower = (loc or '').lower()

        score = 0.0

        # --- A. ROLE TITLE FIT (Max 30 pts) ---
        # Excluded / Avoid: QA / Testing per user directive
        if any(bad in title_lower for bad in ['qa engineer', 'tester', 'test engineer', 'quality assurance', 'test automation', 'sdet']):
            score -= 25.0
        # Excluded: Senior Architect / Director / VP
        elif any(bad in title_lower for bad in ['director', 'principal', 'vp', 'vice president', 'head of', 'chief']):
            score -= 20.0
        elif 'senior' in title_lower or 'lead' in title_lower:
            score -= 10.0
        
        # Positive Title Matches
        if any(t in title_lower for t in ['ai engineer', 'artificial intelligence engineer', 'machine learning engineer', 'ml engineer', 'deep learning']):
            score += 30.0
        elif any(t in title_lower for t in ['computer vision', 'cv engineer', 'nlp engineer', 'conversational ai']):
            score += 30.0
        elif any(t in title_lower for t in ['genai', 'generative ai', 'llm engineer', 'ai developer', 'agentic']):
            score += 28.0
        elif any(t in title_lower for t in ['data scientist', 'python developer', 'ai researcher', 'applied ai']):
            score += 25.0
        elif any(t in title_lower for t in ['data analyst', 'bi analyst', 'analytics engineer', 'data engineer']):
            score += 15.0
        elif any(t in title_lower for t in ['software engineer', 'backend engineer', 'developer', 'full stack']):
            score += 12.0
        else:
            score += 5.0

        # --- B. TECH STACK & SKILL ALIGNMENT (Max 35 pts) ---
        # Python
        if re.search(r'\bpython\b', text_corpus):
            score += 7.0
        # PyTorch / Deep Learning
        if re.search(r'\b(pytorch|deep learning|neural networks)\b', text_corpus):
            score += 7.0
        # LLMs / GenAI / RAG / Transformers
        if re.search(r'\b(llm|llms|generative ai|genai|rag|langchain|transformer|gpt|gemini|claude)\b', text_corpus):
            score += 7.0
        # Computer Vision / NLP
        if re.search(r'\b(computer vision|opencv|yolo|ocr|nlp|natural language processing)\b', text_corpus):
            score += 5.0
        # API / Deployment: FastAPI, Docker, Modal, Cloud
        if re.search(r'\b(fastapi|flask|rest|docker|modal|aws|azure|gcp|cloud)\b', text_corpus):
            score += 5.0
        # SQL / Data Wrangling
        if re.search(r'\b(sql|postgres|mysql|pandas|data analysis)\b', text_corpus):
            score += 4.0

        # --- C. EXPERIENCE & SENIORITY FIT (Max 20 pts) ---
        if any(e in title_lower or e in text_corpus for e in ['intern', 'internship', 'graduate', 'fresh', 'entry level', 'junior', 'trainee', '0-1', '0-2', '0 to 2']):
            score += 20.0
        elif 'associate' in title_lower or 'entry' in sen_lower or 'associate' in sen_lower:
            score += 16.0
        elif 'mid-senior' in sen_lower:
            score += 5.0
        elif 'not applicable' in sen_lower or not sen_lower:
            score += 10.0

        # --- D. GEOGRAPHY & WORK AUTHORIZATION FIT (Max 15 pts) ---
        if any(k in loc_lower for k in ['saudi', 'riyadh', 'jeddah', 'dammam', 'khobar', 'dhahran', 'ksa']):
            score += 15.0  # Top preference, local resident in Eastern Province / KFUPM with transferable Iqama
        elif any(k in loc_lower for k in ['uae', 'dubai', 'abu dhabi', 'sharjah', 'united arab emirates']):
            score += 12.0  # GCC neighbor, visa sponsorship feasible
        elif 'remote' in loc_lower or 'remote' in title_lower:
            score += 13.0  # B2B contractor / remote eligible
        elif any(k in loc_lower for k in ['india', 'bengaluru', 'hyderabad', 'pune', 'delhi', 'mumbai']):
            score += 14.0  # Full citizen rights
        else:
            score += 5.0

        # Final score bounding
        final_score = max(5.0, min(98.5, score))
        final_score = round(final_score, 1)

        # Status determination
        if final_score >= 75.0:
            status = 'shortlisted'
            shortlisted_count += 1
        elif final_score >= 50.0:
            status = 'evaluated'
            evaluated_count += 1
        else:
            status = 'low_fit'
            low_fit_count += 1

        cur.execute("UPDATE jobs SET match_score = ?, status = ? WHERE id = ?", (final_score, status, jid))

    conn.commit()

    print(f"Scoring Complete:")
    print(f"  - Shortlisted (Score >= 75%): {shortlisted_count}")
    print(f"  - Evaluated / Moderate (Score 50-74%): {evaluated_count}")
    print(f"  - Low Fit (Score < 50%): {low_fit_count}")
    print(f"  - Out of Region (US - No Auth): {tagged_us}")

    # Summary of clean database
    cur.execute("SELECT count(*) FROM jobs")
    total_clean = cur.fetchone()[0]
    print(f"\nTotal Clean Jobs in Database: {total_clean}")

    cur.execute("SELECT source, count(*) FROM jobs GROUP BY source")
    print("\nBreakdown by Source:")
    for src, cnt in cur.fetchall():
        print(f"  {src.upper()}: {cnt}")

    cur.execute("SELECT status, count(*) FROM jobs GROUP BY status")
    print("\nBreakdown by Status:")
    for st, cnt in cur.fetchall():
        print(f"  {st}: {cnt}")

    conn.close()

if __name__ == '__main__':
    clean_and_score()
