import requests
from db import get_db

# Added Indian tech hubs and global remote companies
GREENHOUSE_COMPANIES = ["scaleai", "stripe", "reddit", "discord", "doordash", "instacart", "robinhood", "coinbase", "dropbox", "airbnb", "databricks", "postman", "razorpay", "cred", "swiggy", "zomato", "atlassian"]
LEVER_COMPANIES = ["plaid", "spotify", "netflix", "twitch", "figma", "ramp", "vercel", "palantir", "gitlab", "hashicorp"]
ASHBY_COMPANIES = ["openai", "notion", "supabase", "linear", "replit", "deel"]

TARGET_KEYWORDS = [
    "java", "backend", "software engineer", "intern", "fresher", "graduate", 
    "junior", "entry level", "spring boot", "application developer", 
    "software development engineer", "software developer"
]

BLOCK_KEYWORDS = ["senior", "lead", "manager", "principal", "staff", "director", "architect", "head of"]

def is_target_job(title):
    title_lower = title.lower()
    has_target = any(kw in title_lower for kw in TARGET_KEYWORDS)
    is_blocked = any(bad in title_lower for bad in BLOCK_KEYWORDS)
    return has_target and not is_blocked

def discover():
    print("Scraping Greenhouse, Lever, and Ashby APIs...")
    con = get_db()
    new = 0
    
    # --- 1. GREENHOUSE ---
    print("Scanning Greenhouse...")
    for company in GREENHOUSE_COMPANIES:
        url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                for j in r.json().get("jobs", []):
                    if is_target_job(j['title']):
                        jid = f"gh_{company}_{j['id']}"
                        cur = con.execute(
                            "INSERT OR IGNORE INTO applications (job_id, company, title, url, description, status) VALUES (?,?,?,?,?, 'DISCOVERED')",
                            (jid, company.capitalize(), j['title'], j['absolute_url'], "Greenhouse Job")
                        )
                        new += cur.rowcount
        except Exception:
            pass

    # --- 2. LEVER ---
    print("Scanning Lever...")
    for company in LEVER_COMPANIES:
        url = f"https://api.lever.co/v0/postings/{company}?mode=json"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                for j in r.json():
                    if is_target_job(j['text']):
                        jid = f"lever_{company}_{j['id']}"
                        cur = con.execute(
                            "INSERT OR IGNORE INTO applications (job_id, company, title, url, description, status) VALUES (?,?,?,?,?, 'DISCOVERED')",
                            (jid, company.capitalize(), j['text'], j['hostedUrl'], "Lever Job")
                        )
                        new += cur.rowcount
        except Exception:
            pass

    # --- 3. ASHBY ---
    print("Scanning Ashby...")
    for company in ASHBY_COMPANIES:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{company}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                for j in r.json().get("jobs", []):
                    if is_target_job(j['title']):
                        jid = f"ashby_{company}_{j['id']}"
                        cur = con.execute(
                            "INSERT OR IGNORE INTO applications (job_id, company, title, url, description, status) VALUES (?,?,?,?,?, 'DISCOVERED')",
                            (jid, company.capitalize(), j['title'], j['jobUrl'], "Ashby Job")
                        )
                        new += cur.rowcount
        except Exception:
            pass
            
    con.commit()
    print(f"Found {new} target jobs across all platforms.")

if __name__ == "__main__":
    discover()
