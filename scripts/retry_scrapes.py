import os, sys, time, json, sqlite3, requests, re

API_KEY = 'fc-a437930feeae4864bb0e5194d4a18153'
DB_PATH = 'data/jobs.db'

sys.path.insert(0, os.path.abspath('scripts'))
from test_parser import parse_bayt, parse_indeed, parse_naukri

# The exact targets that were hit by 429 rate limit (Firecrawl free plan is 10 req/min)
RETRY_TARGETS = [
    {'source': 'bayt', 'url': 'https://www.bayt.com/en/saudi-arabia/jobs/deep-learning-jobs/', 'label': 'Bayt KSA Deep Learning'},
    {'source': 'bayt', 'url': 'https://www.bayt.com/en/saudi-arabia/jobs/computer-vision-jobs/', 'label': 'Bayt KSA Computer Vision'},
    {'source': 'bayt', 'url': 'https://www.bayt.com/en/saudi-arabia/jobs/generative-ai-jobs/', 'label': 'Bayt KSA Generative AI'},
    {'source': 'bayt', 'url': 'https://www.bayt.com/en/uae/jobs/artificial-intelligence-jobs/', 'label': 'Bayt UAE AI'},
    {'source': 'bayt', 'url': 'https://www.bayt.com/en/uae/jobs/machine-learning-jobs/', 'label': 'Bayt UAE ML'},
    {'source': 'bayt', 'url': 'https://www.bayt.com/en/uae/jobs/data-science-jobs/', 'label': 'Bayt UAE Data Science'},
    {'source': 'naukri', 'url': 'https://www.naukrigulf.com/artificial-intelligence-jobs-in-saudi-arabia?experience=0', 'label': 'Naukri KSA AI 0-1yr'},
    {'source': 'naukri', 'url': 'https://www.naukrigulf.com/machine-learning-jobs-in-saudi-arabia?experience=0', 'label': 'Naukri KSA ML 0-1yr'},
    {'source': 'naukri', 'url': 'https://www.naukrigulf.com/data-science-jobs-in-saudi-arabia?experience=0', 'label': 'Naukri KSA Data Science 0-1yr'}
]

def clean_key(company, title):
    c = re.sub(r'[^a-zA-Z0-9]', '', company).lower()
    t = re.sub(r'[^a-zA-Z0-9]', '', title).lower()
    return f"{c}_{t}"

def scrape_url(url):
    for attempt in range(3):
        try:
            r = requests.post(
                'https://api.firecrawl.dev/v1/scrape',
                json={'url': url},
                headers={'Authorization': f'Bearer {API_KEY}'},
                timeout=30
            )
            if r.status_code == 200:
                return r.json().get('data', {}).get('markdown', '')
            elif r.status_code == 429:
                print(f"    [Rate limit 429] Backing off 15s (Attempt {attempt+1}/3)...")
                time.sleep(15)
            else:
                print(f"    [HTTP {r.status_code}]: {r.text[:100]}")
                return ''
        except Exception as e:
            print(f"    [Exception]: {e}")
            time.sleep(5)
    return ''

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT company, title FROM jobs")
    existing_keys = set(clean_key(c or '', t or '') for c, t in cur.fetchall())
    print(f"Loaded {len(existing_keys)} existing unique jobs.")

    added = 0
    dups = 0

    for i, target in enumerate(RETRY_TARGETS, 1):
        label = target['label']
        url = target['url']
        source = target['source']
        print(f"[{i}/{len(RETRY_TARGETS)}] Scraping: {label} ...")
        
        md = scrape_url(url)
        if not md:
            time.sleep(7.0)
            continue

        if source == 'bayt':
            jobs = parse_bayt(md)
        elif source == 'naukri':
            jobs = parse_naukri(md)
        else:
            jobs = []

        for job in jobs:
            title = job.get('title', '').strip()
            company = job.get('company', '').strip()
            if not title or not company:
                continue
            ckey = clean_key(company, title)
            if ckey in existing_keys:
                dups += 1
                continue

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
                added += 1
            except sqlite3.IntegrityError:
                dups += 1

        print(f"  -> Added {added} total new unique jobs so far (Skipped {dups} dups)")
        time.sleep(7.0) # Safe pacing to stay under 10 req/min

    cur.execute("SELECT count(*), source FROM jobs GROUP BY source")
    print("Updated Breakdown by Source:", cur.fetchall())
    conn.close()

if __name__ == '__main__':
    main()
