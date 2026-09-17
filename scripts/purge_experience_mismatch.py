import sqlite3
import re
import json
import os
import shutil
import sys

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = 'data/jobs.db'
BACKUP_PATH = 'data/jobs.db.bak_pre_yoe_purge'
AUDIT_LOG_PATH = 'data/deleted_jobs_audit.json'

WORD_TO_NUM = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'eleven': 11, 'twelve': 12, 'fifteen': 15, 'twenty': 20,
    '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    '11': 11, '12': 12, '15': 15, '20': 20
}

PATTERNS = [
    # Pattern 1: Qualifier + number + (optional upper) + years/yrs
    re.compile(
        r'(?:(?:minimum|min\.?|at\s+least|over|more\s+than|approximately|approx\.?|around)\s+(?:of\s+)?)'
        r'(\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen)'
        r'(?:\s*\(\d+\))?'
        r'(?:\s*(?:-|–|—|to|\ufffd|\?)\s*(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen))?'
        r'(?:\s*(?:\+|or\s+more))?'
        r'\s*(?:years?|yrs?)\b',
        re.IGNORECASE
    ),
    # Pattern 2: Number + (+) + years/yrs + (of/in) + (experience/work/engineering...)
    re.compile(
        r'\b(\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen)'
        r'(?:\s*\(\d+\))?'
        r'(?:\s*(?:-|–|—|to|\ufffd|\?)\s*(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen))?'
        r'(?:\s*(?:\+|or\s+more))?'
        r'\s*(?:years?|yrs?)\b'
        r'(?:\s+(?:of|in|with))?'
        r'(?:\s+(?:relevant|hands-on|professional|commercial|industry|work|practical|demonstrated|proven|prior|software|engineering|development|direct|machine\s+learning|ai|data\s+science))?'
        r'(?:\s+experience)?',
        re.IGNORECASE
    ),
    # Pattern 3: "Experience: 3-5 years" or "Experience: 3+ years"
    re.compile(
        r'(?:experience|exp\.?)\s*(?:required|needed|level)?\s*[:\-–—]\s*'
        r'(?:(?:minimum|min\.?|at\s+least)\s+(?:of\s+)?)?'
        r'(\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen)'
        r'(?:\s*(?:-|–|—|to|\ufffd|\?)\s*(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen))?'
        r'(?:\s*(?:\+|or\s+more))?'
        r'\s*(?:years?|yrs?)?',
        re.IGNORECASE
    ),
    # Pattern 4: "X+ years building/working/deploying"
    re.compile(
        r'\b(\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen)'
        r'(?:\s*(?:\+|or\s+more))'
        r'\s*(?:years?|yrs?)\b'
        r'(?:\s+(?:building|working|deploying|applying|leading|designing|architecting|developing|coding))',
        re.IGNORECASE
    )
]

FALSE_POSITIVE_KEYWORDS = [
    'ago', 'founded', 'established', 'company has', 'history', 'anniversary',
    'years old', 'over the past', 'in recent years', 'within 2 years', 'within 3 years',
    'valid for 2 years', 'valid for 3 years', 'warranty', 'age of', 'between 20', 'degree'
]

SENIOR_TITLE_KEYWORDS = ['senior', 'sr.', 'sr ', 'lead', 'principal', 'staff', 'director', 'vp', 'head of', 'chief']
JUNIOR_EXCEPTIONS = ['graduate', 'intern', 'internship', 'junior', 'fresh', 'trainee', 'entry level', 'entry-level', 'new grad']

def run_purge():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return

    # 1. Verify / Create Backup
    if not os.path.exists(BACKUP_PATH):
        shutil.copyfile(DB_PATH, BACKUP_PATH)
        print(f"Created pre-purge backup at {BACKUP_PATH}")
    else:
        print(f"Pre-purge backup already exists at {BACKUP_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT count(*) FROM jobs")
    total_before = cur.fetchone()[0]
    print(f"\nTotal jobs in DB before purge: {total_before}")

    cur.execute('''
        SELECT id, title, company, location, seniority_level, description_text,
               match_score, status, application_folder
        FROM jobs
    ''')
    all_jobs = cur.fetchall()

    to_delete = []

    for row in all_jobs:
        jid, title, comp, loc, sen, desc, score, status, app_folder = row
        desc_str = desc or ''
        title_lower = (title or '').lower()

        # Check JD requirements
        reasons = []
        snippets = []

        for pat in PATTERNS:
            for m in pat.finditer(desc_str):
                start = max(0, m.start() - 35)
                end = min(len(desc_str), m.end() + 35)
                snip = desc_str[start:end].replace('\n', ' ').strip()
                low_snip = snip.lower()

                if any(fp in low_snip for fp in FALSE_POSITIVE_KEYWORDS):
                    if 'experience' not in low_snip:
                        continue

                val1_str = m.group(1).lower() if m.group(1) else None
                val2_str = m.group(2).lower() if len(m.groups()) > 1 and m.group(2) else None

                v1 = WORD_TO_NUM.get(val1_str)
                v2 = WORD_TO_NUM.get(val2_str)

                if v1 is not None and v1 >= 3 and v1 <= 25:
                    reasons.append(f"JD requires >= 3 yrs: '{m.group(0)}'")
                    snippets.append(snip)

        # Check Title Seniority
        is_senior_title = any(w in title_lower for w in SENIOR_TITLE_KEYWORDS)
        is_junior_exception = any(w in title_lower for w in JUNIOR_EXCEPTIONS)

        if is_senior_title and not is_junior_exception:
            reasons.append(f"Senior / Lead title: '{title}'")

        if reasons:
            to_delete.append({
                'id': jid,
                'title': title,
                'company': comp,
                'location': loc,
                'seniority_level': sen,
                'status': status,
                'match_score': score,
                'application_folder': app_folder,
                'reasons': list(set(reasons)),
                'snippets': list(set(snippets))
            })

    print(f"Identified {len(to_delete)} jobs requiring > 2 years experience (or senior titles).")

    # Status breakdown of jobs to be deleted
    from collections import Counter
    status_counts = Counter(j['status'] for j in to_delete)
    print("\nBreakdown of jobs to be deleted by status:")
    for st, cnt in status_counts.items():
        print(f"  - {st}: {cnt}")

    # Save full audit log to disk
    with open(AUDIT_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(to_delete, f, indent=2)
    print(f"\nSaved detailed audit log of deleted jobs to {AUDIT_LOG_PATH}")

    # Execute DELETE
    deleted_count = 0
    for j in to_delete:
        cur.execute("DELETE FROM jobs WHERE id = ?", (j['id'],))
        deleted_count += 1

    conn.commit()

    # Compact database
    cur.execute("VACUUM")
    conn.commit()

    cur.execute("SELECT count(*) FROM jobs")
    total_after = cur.fetchone()[0]

    print(f"\n==================================================")
    print(f"PURGE COMPLETE")
    print(f"==================================================")
    print(f"Deleted jobs: {deleted_count}")
    print(f"Remaining clean jobs in DB: {total_after}")

    print("\nRemaining Status Breakdown:")
    cur.execute("SELECT status, count(*) FROM jobs GROUP BY status ORDER BY count(*) DESC")
    for st, cnt in cur.fetchall():
        print(f"  - {st}: {cnt}")

    print("\nRemaining Shortlisted Jobs:")
    cur.execute("SELECT id, title, company, match_score, seniority_level FROM jobs WHERE status = 'shortlisted' ORDER BY match_score DESC")
    shortlisted = cur.fetchall()
    print(f"Total Shortlisted: {len(shortlisted)}")
    for jid, t, c, sc, sen in shortlisted:
        print(f"  * [{sc}%] {t} @ {c} ({sen})")

    conn.close()

if __name__ == '__main__':
    run_purge()
