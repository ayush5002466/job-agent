import requests
from db import get_db

# Huge lists of companies across 6 platforms
GREENHOUSE_COMPANIES = ["scaleai", "stripe", "reddit", "discord", "doordash", "instacart", "robinhood", "coinbase", "dropbox", "airbnb", "databricks", "postman", "razorpay", "cred", "swiggy", "zomato", "atlassian"]
LEVER_COMPANIES = ["plaid", "spotify", "netflix", "twitch", "figma", "ramp", "vercel", "palantir", "gitlab", "hashicorp"]
ASHBY_COMPANIES = ["openai", "notion", "supabase", "linear", "replit", "deel"]
WORKABLE_COMPANIES = ["turing", "deel", "remote", "canonical", "trustpilot"]
SMARTRECRUITERS_COMPANIES = ["Bosch", "Visa", "McDonalds", "Ubisoft", "Atos"]
RECRUITEE_COMPANIES = ["heyflow", "peak", "bunq", "framer"]

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
    print("Scraping 6 Platforms...")
    con = get_db()
    new = 0

    def insert_job(jid, company, title, url):
        nonlocal new
        cur = con.execute(
            "INSERT OR IGNORE INTO applications (job_id, company, title, url, description, status) VALUES (?,?,?,?,?, 'DISCOVERED')",
            (jid, company.capitalize(), title, url, "API Job")
        )
        new += cur.rowcount

    # 1. GREENHOUSE
    for company in GREENHOUSE_COMPANIES:
        try:
            r = requests.get(f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs", timeout=10)
            if r.status_code == 200:
                for j in r.json().get("jobs", []):
                    if is_target_job(j['title']):
                        insert_job(f"gh_{company}_{j['id']}", company, j['title'], j['absolute_url'])
        except: pass

    # 2. LEVER
    for company in LEVER_COMPANIES:
        try:
            r = requests.get(f"https://api.lever.co/v0/postings/{company}?mode=json", timeout=10)
            if r.status_code == 200:
                for j in r.json():
                    if is_target_job(j['text']):
                        insert_job(f"lever_{company}_{j['id']}", company, j['text'], j['hostedUrl'])
        except: pass

    # 3. ASHBY
    for company in ASHBY_COMPANIES:
        try:
            r = requests.get(f"https://api.ashbyhq.com/posting-api/job-board/{company}", timeout=10)
            if r.status_code == 200:
                for j in r.json().get("jobs", []):
                    if is_target_job(j['title']):
                        insert_job(f"ashby_{company}_{j['id']}", company, j['title'], j['jobUrl'])
        except: pass

    # 4. WORKABLE
    for company in WORKABLE_COMPANIES:
        try:
            r = requests.get(f"https://apply.workable.com/api/v1/widget/accounts/{company}?details=true", timeout=10)
            if r.status_code == 200:
                for j in r.json().get("jobs", []):
                    if is_target_job(j['title']):
                        insert_job(f"workable_{company}_{j['shortcode']}", company, j['title'], j['url'])
        except: pass

    # 5. SMARTRECRUITERS
    for company in SMARTRECRUITERS_COMPANIES:
        try:
            r = requests.get(f"https://api.smartrecruiters.com/v1/companies/{company}/postings?limit=100", timeout=10)
            if r.status_code == 200:
                for j in r.json().get("content", []):
                    if is_target_job(j['name']):
                        insert_job(f"sr_{company}_{j['id']}", company, j['name'], j['ref'])
        except: pass

    # 6. RECRUITEE
    for company in RECRUITEE_COMPANIES:
        try:
            r = requests.get(f"https://{company}.recruitee.com/api/offers/", timeout=10)
            if r.status_code == 200:
                for j in r.json().get("offers", []):
                    if is_target_job(j['title']):
                        insert_job(f"recruitee_{company}_{j['id']}", company, j['title'], j['careers_url'])
        except: pass
            
    con.commit()
    print(f"Found {new} target jobs across all 6 platforms.")

if __name__ == "__main__":
    discover()
