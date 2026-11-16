import json, os, yaml, time, requests
from bs4 import BeautifulSoup
from groq import Groq
from db import get_db, update_status

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
profile = yaml.safe_load(open("profile.yaml"))

def score_pending():
    con = get_db()
    # Increased LIMIT from 15 to 50 to clear the backlog faster
    jobs = con.execute("SELECT * FROM applications WHERE status='DISCOVERED' LIMIT 50").fetchall()
    
    for j in jobs:
        print(f"Fetching details for {j['title']} @ {j['company']}...")
        try:
            r = requests.get(j['url'], timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            description = ' '.join(soup.stripped_strings)[:3000] 
        except Exception:
            description = "Could not load description."
            
        print(f"Scoring {j['title']}...")
        
        # HYPER-AGGRESSIVE PROMPT
        prompt = f"""You are an aggressive career coach. The candidate wants to apply to everything. Score this job 0-100.
CANDIDATE: {yaml.dump(profile)}
JOB DESCRIPTION: {description}

STRICT SCORING RULES (DO NOT DEVIATE):
1. If the job title contains "Intern" or "New Grad" or "Graduate", you MUST give it a score between 80 and 100.
2. If the job title contains "Software", "Backend", "Java", or "Developer", you MUST give it a score between 50 and 70.
3. Ignore ALL "years of experience" requirements. We want to apply anyway.
4. Only give a score below 30 if it strictly requires a PhD, a US Security Clearance, or is a non-technical role (like Sales or HR).

Return JSON only: {{"score": int, "rationale": "1 sentence"}}"""
        
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"}
            )
            text = chat_completion.choices[0].message.content
            data = json.loads(text)
            
            # Threshold is 40
            new_status = "SCORED" if data["score"] >= 40 else "REJECTED"
            update_status(con, j["job_id"], new_status, score=data["score"], rationale=data["rationale"])
            print(f" -> Score: {data['score']} ({new_status})")
        except Exception as e:
            print(f" -> Failed to parse: {e}")
        time.sleep(1) # Reduced sleep because Groq is fast
