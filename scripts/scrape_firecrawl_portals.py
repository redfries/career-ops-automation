import os, sys, time, json, sqlite3, requests, re

API_KEY = 'fc-a437930feeae4864bb0e5194d4a18153'
DB_PATH = 'data/jobs.db'

# Import parser functions
sys.path.insert(0, os.path.abspath('scripts'))
from test_parser import parse_bayt, parse_indeed, parse_naukri

# Curated Orthogonal Target Slices
TARGET_URLS = [
    # --- BAYT CATEGORY SLICES (Saudi Arabia) ---
    {'source': 'bayt', 'url': 'https://www.bayt.com/en/saudi-arabia/jobs/artificial-intelligence-jobs/', 'label': 'Bayt KSA AI Page 1'},
    {'source': 'bayt', 'url': 'https://www.bayt.com/en/saudi-arabia/jobs/artificial-intelligence-jobs/?page=2', 'label': 'Bayt KSA AI Page 2'},
    {'source': 'bayt', 'url': 'https://www.bayt.com/en/saudi-arabia/jobs/machine-learning-jobs/', 'label': 'Bayt KSA ML Page 1'},
    {'source': 'bayt', 'url': 'https://www.bayt.com/en/saudi-arabia/jobs/machine-learning-jobs/?page=2', 'label': 'Bayt KSA ML Page 2'},
    {'source': 'bayt', 'url': 'https://www.bayt.com/en/saudi-arabia/jobs/data-science-jobs/', 'label': 'Bayt KSA Data Science Page 1'},
    {'source': 'bayt', 'url': 'https://www.bayt.com/en/saudi-arabia/jobs/data-science-jobs/?page=2', 'label': 'Bayt KSA Data Science Page 2'},
    {'source': 'bayt', 'url': 'https://www.bayt.com/en/saudi-arabia/jobs/deep-learning-jobs/', 'label': 'Bayt KSA Deep Learning'},
    {'source': 'bayt', 'url': 'https://www.bayt.com/en/saudi-arabia/jobs/computer-vision-jobs/', 'label': 'Bayt KSA Computer Vision'},
    {'source': 'bayt', 'url': 'https://www.bayt.com/en/saudi-arabia/jobs/generative-ai-jobs/', 'label': 'Bayt KSA Generative AI'},

    # --- BAYT UAE SLICES ---
    {'source': 'bayt', 'url': 'https://www.bayt.com/en/uae/jobs/artificial-intelligence-jobs/', 'label': 'Bayt UAE AI'},
    {'source': 'bayt', 'url': 'https://www.bayt.com/en/uae/jobs/machine-learning-jobs/', 'label': 'Bayt UAE ML'},
    {'source': 'bayt', 'url': 'https://www.bayt.com/en/uae/jobs/data-science-jobs/', 'label': 'Bayt UAE Data Science'},

    # --- NAUKRIGULF STRICT EXPERIENCE=0 (FRESHERS/GRADUATES) ---
    {'source': 'naukri', 'url': 'https://www.naukrigulf.com/artificial-intelligence-jobs-in-saudi-arabia?experience=0', 'label': 'Naukri KSA AI 0-1yr'},
    {'source': 'naukri', 'url': 'https://www.naukrigulf.com/machine-learning-jobs-in-saudi-arabia?experience=0', 'label': 'Naukri KSA ML 0-1yr'},
    {'source': 'naukri', 'url': 'https://www.naukrigulf.com/data-science-jobs-in-saudi-arabia?experience=0', 'label': 'Naukri KSA Data Science 0-1yr'},
    {'source': 'naukri', 'url': 'https://www.naukrigulf.com/python-developer-jobs-in-saudi-arabia?experience=0', 'label': 'Naukri KSA Python 0-1yr'},
    {'source': 'naukri', 'url': 'https://www.naukrigulf.com/artificial-intelligence-jobs-in-uae?experience=0', 'label': 'Naukri UAE AI 0-1yr'},
    {'source': 'naukri', 'url': 'https://www.naukrigulf.com/machine-learning-jobs-in-uae?experience=0', 'label': 'Naukri UAE ML 0-1yr'},
    {'source': 'naukri', 'url': 'https://www.naukrigulf.com/data-science-jobs-in-uae?experience=0', 'label': 'Naukri UAE Data Science 0-1yr'},

    # --- INDEED KSA ORTHOGONAL SLICES (ENTRY_LEVEL) ---
    {'source': 'indeed', 'url': 'https://sa.indeed.com/jobs?q=AI+machine+learning&l=Saudi+Arabia&explvl=ENTRY_LEVEL', 'label': 'Indeed KSA AI/ML Entry'},
    {'source': 'indeed', 'url': 'https://sa.indeed.com/jobs?q=graduate+AI+OR+%22machine+learning%22&l=Saudi+Arabia', 'label': 'Indeed KSA Graduate AI/ML'},
    {'source': 'indeed', 'url': 'https://sa.indeed.com/jobs?q=%22computer+vision%22+OR+NLP&l=Saudi+Arabia&explvl=ENTRY_LEVEL', 'label': 'Indeed KSA Vision/NLP Entry'},
    {'source': 'indeed', 'url': 'https://sa.indeed.com/jobs?q=AI+intern&l=Saudi+Arabia', 'label': 'Indeed KSA AI Intern'},
    {'source': 'indeed', 'url': 'https://sa.indeed.com/jobs?q=junior+machine+learning&l=Saudi+Arabia', 'label': 'Indeed KSA Junior ML'},
    {'source': 'indeed', 'url': 'https://sa.indeed.com/jobs?q=data+scientist&l=Riyadh&explvl=ENTRY_LEVEL', 'label': 'Indeed Riyadh Data Scientist Entry'},
    {'source': 'indeed', 'url': 'https://sa.indeed.com/jobs?q=machine+learning&l=Dhahran&explvl=ENTRY_LEVEL', 'label': 'Indeed Dhahran/Eastern ML'},
    {'source': 'indeed', 'url': 'https://sa.indeed.com/jobs?q=artificial+intelligence&l=Jeddah&explvl=ENTRY_LEVEL', 'label': 'Indeed Jeddah AI Entry'},

    # --- INDEED UAE ORTHOGONAL SLICES (ENTRY_LEVEL) ---
    {'source': 'indeed', 'url': 'https://ae.indeed.com/jobs?q=AI+machine+learning&l=United+Arab+Emirates&explvl=ENTRY_LEVEL', 'label': 'Indeed UAE AI/ML Entry'},
    {'source': 'indeed', 'url': 'https://ae.indeed.com/jobs?q=graduate+AI+OR+%22machine+learning%22&l=Dubai', 'label': 'Indeed Dubai Graduate AI'},
    {'source': 'indeed', 'url': 'https://ae.indeed.com/jobs?q=junior+AI+engineer&l=United+Arab+Emirates', 'label': 'Indeed UAE Junior AI'}
]

def scrape_url(url):
    try:
        r = requests.post(
            'https://api.firecrawl.dev/v1/scrape',
            json={'url': url},
            headers={'Authorization': f'Bearer {API_KEY}'},
            timeout=30
        )
        if r.status_code == 200:
            return r.json().get('data', {}).get('markdown', '')
        else:
            print(f"    [HTTP {r.status_code}] Failed: {r.text[:120]}")
            return ''
    except Exception as e:
        print(f"    [Exception]: {e}")
        return ''

def clean_key(company, title):
    # Normalize company and title for collision checking
    c = re.sub(r'[^a-zA-Z0-9]', '', company).lower()
    t = re.sub(r'[^a-zA-Z0-9]', '', title).lower()
    return f"{c}_{t}"

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Load existing keys from database to avoid duplicates
    cur.execute("SELECT company, title FROM jobs")
    existing_keys = set(clean_key(c or '', t or '') for c, t in cur.fetchall())
    print(f"Loaded {len(existing_keys)} existing unique jobs from DB.")

    total_scraped_raw = 0
    total_new_inserted = 0
    total_duplicates_dropped = 0

    for i, target in enumerate(TARGET_URLS, 1):
        label = target['label']
        url = target['url']
        source = target['source']
        print(f"\n[{i}/{len(TARGET_URLS)}] Scraping: {label} ...")
        
        md = scrape_url(url)
        if not md:
            time.sleep(1.5)
            continue

        if source == 'bayt':
            jobs = parse_bayt(md)
        elif source == 'indeed':
            jobs = parse_indeed(md)
        elif source == 'naukri':
            jobs = parse_naukri(md)
        else:
            jobs = []

        total_scraped_raw += len(jobs)
        print(f"  -> Extracted {len(jobs)} jobs from page.")

        slice_new = 0
        slice_dups = 0

        for job in jobs:
            title = job.get('title', '').strip()
            company = job.get('company', '').strip()
            if not title or not company:
                continue

            ckey = clean_key(company, title)
            if ckey in existing_keys:
                slice_dups += 1
                total_duplicates_dropped += 1
                continue

            # It is truly unique! Insert into SQLite
            location = job.get('location', 'Saudi Arabia / UAE')
            job_url = job.get('url', '')
            desc = job.get('description', '')

            try:
                cur.execute('''
                    INSERT INTO jobs (
                        title, company, location, source, job_url,
                        seniority_level, description_text, status
                    ) VALUES (?, ?, ?, ?, ?, 'Entry level / Graduate', ?, 'scraped')
                ''', (title, company, location, source, job_url, desc))
                conn.commit()
                existing_keys.add(ckey)
                slice_new += 1
                total_new_inserted += 1
            except sqlite3.IntegrityError:
                slice_dups += 1
                total_duplicates_dropped += 1

        print(f"  -> Added {slice_new} NEW unique jobs | Skipped {slice_dups} duplicates/seen.")
        time.sleep(2.0)  # Gentle spacing between Firecrawl calls

    cur.execute("SELECT count(*), source FROM jobs GROUP BY source")
    summary = cur.fetchall()
    conn.close()

    print("\n==========================================")
    print("FINISHED MULTI-PORTAL SCRAPE & INGESTION")
    print(f"Total Raw Jobs Extracted: {total_scraped_raw}")
    print(f"Total Duplicate/Overlap Drops: {total_duplicates_dropped}")
    print(f"Total Brand New Unique Jobs Added: {total_new_inserted}")
    print("Database Breakdown by Source:")
    for count, src in summary:
        print(f"  - {src.upper()}: {count} jobs")
    print("==========================================")

if __name__ == '__main__':
    main()
