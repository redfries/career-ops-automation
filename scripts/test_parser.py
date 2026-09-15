import re

def parse_bayt(md):
    pattern = re.compile(r'##\s+\[(.*?)\]\((https://www\.bayt\.com/en/[^\)]+?)(?:\s+"[^"]*")?\)\s*\n+([^\n]+)(.*?)(?=(?:##\s+\[|\Z))', re.DOTALL)
    jobs = []
    for match in pattern.finditer(md):
        title = match.group(1).strip()
        url = match.group(2).strip()
        company = match.group(3).strip()
        body = match.group(4).strip()
        # Clean company if it has markdown formatting
        company = re.sub(r'\[.*?\]\(.*?\)', '', company).strip()
        if not company:
            company = "Confidential Company"
        jobs.append({
            'title': title,
            'company': company,
            'url': url,
            'description': body[:1000]
        })
    return jobs

def parse_indeed(md):
    # Pattern: ### [Title](url)<br>Company<br>Location
    pattern = re.compile(r'###\s+\[(.*?)\]\((https://(?:sa|ae)\.indeed\.com/[^\)]+?)\)<br>([^<]+)<br>([^\n]+)(.*?)(?=(?:###\s+\[|\Z))', re.DOTALL)
    jobs = []
    for match in pattern.finditer(md):
        title = match.group(1).strip()
        url = match.group(2).strip()
        company = match.group(3).strip()
        location = match.group(4).strip()
        body = match.group(5).strip()
        jobs.append({
            'title': title,
            'company': company,
            'location': location,
            'url': url,
            'description': body[:1000]
        })
    return jobs

def parse_naukri(md):
    # Pattern: [Job Title](https://www.naukrigulf.com/...)\s*(\[Company\]|Company)
    pattern = re.compile(r'\[(.*?)\]\((https://www\.naukrigulf\.com/[^)]+?-jid-[^)]+?)\)\s*(?:\[([^\]]+)\]|\s*([^\n\r]+))', re.DOTALL)
    jobs = []
    for match in pattern.finditer(md):
        title = match.group(1).strip()
        url = match.group(2).strip()
        company = (match.group(3) or match.group(4) or '').strip()
        company = re.sub(r'\(.*?\)', '', company).strip()
        if not company or 'Login' in company or 'Register' in company:
            continue
        jobs.append({
            'title': title,
            'company': company,
            'url': url,
            'description': ''
        })
    return jobs

if __name__ == '__main__':
    with open('scratch_bayt.md', 'r', encoding='utf-8') as f:
        bayt_md = f.read()
    b_jobs = parse_bayt(bayt_md)
    print(f'Bayt jobs parsed: {len(b_jobs)}')
    if b_jobs:
        print('Sample Bayt:', b_jobs[0])

    with open('scratch_indeed.md', 'r', encoding='utf-8') as f:
        indeed_md = f.read()
    i_jobs = parse_indeed(indeed_md)
    print(f'Indeed jobs parsed: {len(i_jobs)}')
    if i_jobs:
        print('Sample Indeed:', i_jobs[0])

    with open('scratch_naukri.md', 'r', encoding='utf-8') as f:
        naukri_md = f.read()
    n_jobs = parse_naukri(naukri_md)
    print(f'Naukri jobs parsed: {len(n_jobs)}')
    if n_jobs:
        print('Sample Naukri:', n_jobs[0])
