import json, os, yaml, time, requests
from bs4 import BeautifulSoup
from groq import Groq
from db import get_db, update_status

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

profile = {"name": "Ayush Saraswat", "skills": ["Java", "Python", "Spring Boot"]}

# Only prioritize tech-related internships, skip finance/HR
PRIORITY_KEYWORDS = ["intern", "new grad", "graduate", "fresher", "junior", "entry level", "trainee", "apprentice"]
TECH_KEYWORDS = ["software", "developer", "backend", "frontend", "java", "python", "engineer", "data", "cloud", "devops", "tech"]

def is_priority(title):
    title_lower = title.lower()
    has_priority = any(kw in title_lower for kw in PRIORITY_KEYWORDS)
    has_tech = any(kw in title_lower for kw in TECH_KEYWORDS)
    return has_priority and has_tech

def score_pending():
    con = get_db()
    jobs = con.execute("SELECT * FROM applications WHERE status='DISCOVERED' LIMIT 50").fetchall()
    print(f"Found {len(jobs)} DISCOVERED jobs to process.")
    
    for j in jobs:
        try:
            # TECH PRIORITY BYPASS
            if is_priority(j['title']):
                print(f"⭐ PRIORITY: {j['title']} @ {j['company']} — auto-scoring 85")
                update_status(con, j["job_id"], "SCORED", score=85, rationale="Priority tech job. Auto-scored.")
                continue
            
            print(f"Fetching details for {j['title']} @ {j['company']}...")
            try:
                r = requests.get(j['url'], timeout=10)
                soup = BeautifulSoup(r.text, 'html.parser')
                description = ' '.join(soup.stripped_strings)[:3000] 
            except Exception:
                description = "Could not load description."
                
            print(f"Scoring {j['title']}...")
            
            prompt = f"""Score this job 0-100 for fit.
CANDIDATE: {json.dumps(profile)}
JOB: {description}

RULES:
- Software/Backend/Java/Developer: score 50-70
- Ignore years of experience
- Only score below 30 if: requires PhD, US Security Clearance, or is non-technical

Return JSON only: {{"score": int, "rationale": "1 sentence"}}"""
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"}
            )
            text = chat_completion.choices[0].message.content
            data = json.loads(text)
            new_status = "SCORED" if data["score"] >= 40 else "REJECTED"
            update_status(con, j["job_id"], new_status, score=data["score"], rationale=data["rationale"])
            print(f" -> Score: {data['score']} ({new_status})")
            
        except Exception as e:
            print(f" -> Error processing {j['title']}: {e}")
        time.sleep(1)
