import sqlite3, json, sys, os

def ingest_json_file(file_path):
    if not os.path.exists(file_path):
        print(f'File not found: {file_path}')
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        print('Expected a JSON list of job objects.')
        return
    
    conn = sqlite3.connect('data/jobs.db')
    cur = conn.cursor()
    
    inserted = 0
    skipped_duplicates = 0
    
    for item in data:
        job_id = str(item.get('id', '') or '')
        title = item.get('title', '').strip()
        company = item.get('companyName', '').strip()
        if not title or not company:
            continue
            
        location = item.get('location', '')
        job_url = item.get('link', '') or item.get('url', '')
        posted_date = item.get('postedAt', '')
        applicants = item.get('applicantsCount', '')
        seniority = item.get('seniorityLevel', '')
        emp_type = item.get('employmentType', '')
        industries = item.get('industries', '')
        desc = item.get('descriptionText', '').strip()
        comp_web = item.get('companyWebsite', '')
        comp_desc = item.get('companyDescription', '')
        
        try:
            cur.execute('''
                INSERT INTO jobs (
                    id, title, company, location, source, job_url, posted_date,
                    applicants_count, seniority_level, employment_type,
                    industries, description_text, company_website, company_description
                ) VALUES (?, ?, ?, ?, 'linkedin', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_id, title, company, location, job_url, posted_date,
                applicants, seniority, emp_type, industries, desc, comp_web, comp_desc
            ))
            inserted += 1
        except sqlite3.IntegrityError:
            skipped_duplicates += 1
            
    conn.commit()
    
    cur.execute('SELECT COUNT(*) FROM jobs')
    total = cur.fetchone()[0]
    conn.close()
    
    print(f'Ingest Summary:')
    print(f'  - Newly Inserted: {inserted}')
    print(f'  - Skipped Duplicates: {skipped_duplicates}')
    print(f'  - Total Unique Jobs in DB: {total}')

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'data/scraped_jobs.json'
    ingest_json_file(target)
