import json, os, yaml, time, requests
from bs4 import BeautifulSoup
from google import genai
from db import get_db, update_status

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
profile = yaml.safe_load(open("profile.yaml"))

def score_pending():
    con = get_db()
    # Only score 3 jobs per run
    jobs = con.execute("SELECT * FROM applications WHERE status='DISCOVERED' LIMIT 3").fetchall()
    
    for j in jobs:
        print(f"Fetching details for {j['title']} @ {j['company']}...")
        
        try:
            r = requests.get(j['url'], timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            description = ' '.join(soup.stripped_strings)[:4000] 
        except Exception as e:
            print(f" -> Failed to fetch page: {e}")
            description = "Could not load description."
            
        print(f"Scoring {j['title']}...")
        prompt = f"Score this job 0-100 for fit. Return JSON only: {{\"score\": int, \"rationale\": \"1 sentence\"}}\n\nCANDIDATE: {yaml.dump(profile)}\n\nJOB DESCRIPTION: {description}"
        
        try:
            r = client.models.generate_content(model="gemini-3.8-flash", contents=prompt)
            text = r.text.strip().removeprefix("```json").removesuffix("```").strip()
            data = json.loads(text)
            new_status = "SCORED" if data["score"] >= 70 else "REJECTED"
            update_status(con, j["job_id"], new_status, score=data["score"], rationale=data["rationale"])
            print(f" -> Score: {data['score']} ({new_status})")
        except Exception as e:
            if "429" in str(e):
                print("\n🚨 DAILY API LIMIT REACHED (429). Stopping scoring for now to protect the account.\n")
                break # THIS STOPS THE LOOP IMMEDIATELY
            else:
                print(f" -> Failed to parse: {e}")
                
        time.sleep(4)
