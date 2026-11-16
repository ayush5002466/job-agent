import json, os, yaml, time, requests
from bs4 import BeautifulSoup
from groq import Groq
from db import get_db, update_status

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
profile = yaml.safe_load(open("profile.yaml"))

def score_pending():
    con = get_db()
    jobs = con.execute("SELECT * FROM applications WHERE status='DISCOVERED' LIMIT 15").fetchall()
    
    for j in jobs:
        print(f"Fetching details for {j['title']} @ {j['company']}...")
        try:
            r = requests.get(j['url'], timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            description = ' '.join(soup.stripped_strings)[:4000] 
        except Exception:
            description = "Could not load description."
            
        print(f"Scoring {j['title']}...")
        
        # NEW AGGRESSIVE PROMPT
        prompt = f"""You are a bold career coach. Score this job 0-100 for fit.
CANDIDATE: {yaml.dump(profile)}
JOB DESCRIPTION: {description}

RULES:
- If the title contains "Software", "Backend", "Java", or "Developer", give it AT LEAST a 50.
- If it says "Intern" or "New Grad", give it AT LEAST a 70.
- Ignore the 'years of experience' requirements. We want to apply anyway.
- Only give a score below 40 if it strictly requires a PhD, a US Security Clearance, or is not a software/tech role.
Return JSON only: {{"score": int, "rationale": "1 sentence"}}"""
        
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"}
            )
            text = chat_completion.choices[0].message.content
            data = json.loads(text)
            # LOWERED THRESHOLD TO 40
            new_status = "SCORED" if data["score"] >= 40 else "REJECTED"
            update_status(con, j["job_id"], new_status, score=data["score"], rationale=data["rationale"])
            print(f" -> Score: {data['score']} ({new_status})")
        except Exception as e:
            print(f" -> Failed to parse: {e}")
        time.sleep(2)
