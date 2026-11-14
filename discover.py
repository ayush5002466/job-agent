import requests
from db import get_db

def discover():
    print("Scraping Greenhouse API directly...")
    
    # A list of companies that use Greenhouse and have public APIs
    companies = ["scaleai", "stripe", "reddit", "discord", "doordash", "instacart", "robinhood", "coinbase", "dropbox", "airbnb"]
    
    con = get_db()
    new = 0
    
    for company in companies:
        url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                jobs = r.json().get("jobs", [])
                for j in jobs:
                    jid = f"gh_{company}_{j['id']}"
                    title = j['title'].lower()
                    # Only look for software/intern roles
                    if "engineer" in title or "intern" in title or "software" in title:
                        cur = con.execute(
                            "INSERT OR IGNORE INTO applications (job_id, company, title, url, description, status) VALUES (?,?,?,?,?, 'DISCOVERED')",
                            (jid, company.capitalize(), j['title'], j['absolute_url'], "Greenhouse API Job")
                        )
                        new += cur.rowcount
        except Exception as e:
            print(f"Failed to fetch {company}: {e}")
            
    con.commit()
    print(f"Found {new} new jobs directly from Greenhouse.")

if __name__ == "__main__":
    discover()