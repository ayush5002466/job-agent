import hashlib
from jobspy import scrape_jobs
from db import get_db

def discover():
    print("Scraping jobs...")
    df = scrape_jobs(
        site_name=["indeed"],
        search_term="software engineer intern",
        location="India",
        results_wanted=5,
        hours_old=72,
    )
    con = get_db()
    new = 0
    for _, j in df.iterrows():
        jid = hashlib.sha256(f"{j['company']}|{j['title']}".lower().encode()).hexdigest()[:16]
        cur = con.execute(
            "INSERT OR IGNORE INTO applications (job_id, company, title, url, description, status) VALUES (?,?,?,?,?, 'DISCOVERED')",
            (jid, j["company"], j["title"], j["job_url"], str(j.get("description",""))[:3000])
        )
        new += cur.rowcount
    con.commit()
    print(f"Found {new} new jobs.")
