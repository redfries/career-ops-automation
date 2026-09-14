import json, urllib.request, time, os, sys

def get_token():
    auth_file = r'C:\Users\lords\.mcp-auth\mcp-remote-v1\a105b89723aa1052de19a1f912a7e947_tokens.json'
    with open(auth_file, 'r', encoding='utf-8') as f:
        return json.load(f)['access_token']

def start_scrape():
    token = get_token()
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    actor_id = 'curious_coder~linkedin-jobs-scraper'
    urls = [
        'https://www.linkedin.com/jobs/search/?keywords=(graduate%20OR%20junior%20OR%20intern%20OR%20fresher)%20AND%20(%22machine%20learning%22%20OR%20AI%20OR%20%22computer%20vision%22)&location=Saudi%20Arabia&f_E=1%2C2&f_TPR=r2592000',
        'https://www.linkedin.com/jobs/search/?keywords=%22Graduate%20AI%22%20OR%20%22AI%20Intern%22%20OR%20%22Junior%20AI%22&location=Saudi%20Arabia&f_E=1%2C2',
        'https://www.linkedin.com/jobs/search/?keywords=(graduate%20OR%20junior%20OR%20intern)%20AND%20(%22machine%20learning%22%20OR%20AI)&location=United%20Arab%20Emirates&f_E=1%2C2',
        'https://www.linkedin.com/jobs/search/?keywords=(junior%20OR%20intern)%20AND%20(%22machine%20learning%22%20OR%20%22AI%20Engineer%22)&f_WT=2&f_E=1%2C2'
    ]

    payload = {
        'autoConvertToAiSearch': False,
        'limitPerSource': 250,
        'scrapeCompany': True,
        'splitByLocation': False,
        'under10Applicants': False,
        'urls': urls,
        'datePosted': 'anyTime',
        'companyIds': []
    }

    print(f'Starting Apify Actor run across {len(urls)} target URLs (targeting up to 1,000 jobs)...')
    req = urllib.request.Request(
        f'https://api.apify.com/v2/acts/{actor_id}/runs',
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )

    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        run_data = res['data']
        run_id = run_data['id']
        dataset_id = run_data['defaultDatasetId']
        print(f'Run launched successfully! Run ID: {run_id}')
        print(f'Default Dataset ID: {dataset_id}')

    # Poll until finished
    start_time = time.time()
    while True:
        status_req = urllib.request.Request(
            f'https://api.apify.com/v2/actor-runs/{run_id}',
            headers=headers
        )
        with urllib.request.urlopen(status_req) as s_resp:
            status_data = json.loads(s_resp.read().decode('utf-8'))['data']
            status = status_data['status']
            elapsed = int(time.time() - start_time)
            print(f'[{elapsed}s] Status: {status}')

            if status in ['SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT']:
                break
        time.sleep(10)

    if status != 'SUCCEEDED':
        print(f'Run did not succeed (status={status}). Exiting.')
        return

    # Fetch dataset items
    print('Run completed! Downloading scraped dataset...')
    items_req = urllib.request.Request(
        f'https://api.apify.com/v2/datasets/{dataset_id}/items?clean=true&format=json',
        headers=headers
    )
    with urllib.request.urlopen(items_req) as d_resp:
        items = json.loads(d_resp.read().decode('utf-8'))
        print(f'Downloaded {len(items)} job items!')

    os.makedirs('data', exist_ok=True)
    out_file = 'data/fresh_linkedin_jobs.json'
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f'Saved raw dataset to {out_file}')

    # Ingest into SQLite database
    from ingest_jobs import ingest_json_file
    ingest_json_file(out_file)

if __name__ == '__main__':
    start_scrape()
