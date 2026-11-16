import json, os, yaml, time, requests
from bs4 import BeautifulSoup
from google import genai
from db import get_db, update_status

KEYS = [v for k, v in os.environ.items() if k.startswith("GEMINI_API_KEY") and v]
current_key_index = 0
client = genai.Client(api_key=KEYS[current_key_index])
profile = yaml.safe_load(open("profile.yaml"))

def score_pending():
    global current_key_index, client
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
        
        prompt = f"""You are an encouraging career coach. Score this job 0-100 for fit based on this candidate.
CANDIDATE: {yaml.dump(profile)}
JOB DESCRIPTION: {description}

RULES:
- If it's a Java/Backend/Software role for New Grads or Juniors, give it at least a 60.
- If it's an Internship, give it at least a 70.
- Only give a score below 50 if it strictly requires 5+ years of experience, a PhD, or a US Security Clearance.
Return JSON only: {{"score": int, "rationale": "1 sentence"}}"""
        
        try:
            r = client.models.generate_content(model="gemini-3.8-flash", contents=prompt)
            text = r.text.strip().removeprefix("```json").removesuffix("```").strip()
            data = json.loads(text)
            new_status = "SCORED" if data["score"] >= 60 else "REJECTED"
            update_status(con, j["job_id"], new_status, score=data["score"], rationale=data["rationale"])
            print(f" -> Score: {data['score']} ({new_status})")
        except Exception as e:
            if "429" in str(e) or "503" in str(e):
                current_key_index += 1
                if current_key_index >= len(KEYS):
                    print("\n🚨 ALL API KEYS EXHAUSTED. Stopping scoring for today.\n")
                    break 
                print(f"\n🔄 Limit hit. Rotating to API Key #{current_key_index + 1}...\n")
                client = genai.Client(api_key=KEYS[current_key_index]) 
                time.sleep(2) 
            else:
                print(f" -> Failed to parse: {e}")
        time.sleep(3)
