import requests
from db import get_db

def discover():
    print("Scraping Remote OK API (reliable cloud source)...")
    con = get_db()
    new = 0
    
    try:
        # Using RemoteOK's public JSON API
        r = requests.get("https://remoteok.com/api", headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if r.status_code == 200:
            jobs = r.json()
            for j in jobs:
                if not isinstance(j, dict) or 'position' not in j:
                    continue
                
                title = j.get('position', '')
                company = j.get('company', 'Unknown')
                url = j.get('url', '')
                
                # Only look for software/backend/java roles
                title_lower = title.lower()
                if any(kw in title_lower for kw in ["java", "backend", "software", "developer", "intern"]):
                    jid = f"remoteok_{j.get('id', '')}"
                    cur = con.execute(
                        "INSERT OR IGNORE INTO applications (job_id, company, title, url, description, status) VALUES (?,?,?,?,?, 'DISCOVERED')",
                        (jid, company, title, url, j.get('description', '')[:3000])
                    )
                    new += cur.rowcount
        else:
            print(f"RemoteOK API returned status: {r.status_code}")
    except Exception as e:
        print(f"Failed to fetch RemoteOK: {e}")
        
    con.commit()
    print(f"Found {new} new jobs from RemoteOK.")

if __name__ == "__main__":
    discover()
