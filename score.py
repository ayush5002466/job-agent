import json, os, yaml, time, requests
from bs4 import BeautifulSoup
from google import genai
from db import get_db, update_status

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
profile = yaml.safe_load(open("profile.yaml"))

def score_pending():
    con = get_db()
    # Limit to 15 jobs per cycle so we don't get rate-limited or timeout
    jobs = con.execute("SELECT * FROM applications WHERE status='DISCOVERED' LIMIT 15").fetchall()
    
    for j in jobs:
        print(f"Fetching details for {j['title']} @ {j['company']}...")
        
        # 1. Fetch the actual job description from the URL
        try:
            r = requests.get(j['url'], timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            # Extract text and remove extra spaces/newlines
            description = ' '.join(soup.stripped_strings)[:4000] 
        except Exception as e:
            print(f" -> Failed to fetch page: {e}")
            description = "Could not load description."
            
        print(f"Scoring {j['title']}...")
        prompt = f"Score this job 0-100 for fit. Return JSON only: {{\"score\": int, \"rationale\": \"1 sentence\"}}\n\nCANDIDATE: {yaml.dump(profile)}\n\nJOB DESCRIPTION: {description}"
        
        success = False
        retries = 3
        while not success and retries > 0:
            try:
                r = client.models.generate_content(model="gemini-3.8-flash", contents=prompt)
                text = r.text.strip().removeprefix("```json").removesuffix("```").strip()
                data = json.loads(text)
                new_status = "SCORED" if data["score"] >= 70 else "REJECTED"
                update_status(con, j["job_id"], new_status, score=data["score"], rationale=data["rationale"])
                print(f" -> Score: {data['score']} ({new_status})")
                success = True
            except Exception as e:
                if "503" in str(e):
                    print(" -> Google API busy (503). Retrying in 5s...")
                    time.sleep(5)
                    retries -= 1
                else:
                    print(f" -> Failed to parse: {e}")
                    break
        time.sleep(4)
