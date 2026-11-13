import json, os, yaml
from google import genai
from db import get_db, update_status

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
profile = yaml.safe_load(open("profile.yaml"))

def score_pending():
    con = get_db()
    jobs = con.execute("SELECT * FROM applications WHERE status='DISCOVERED'").fetchall()
    for j in jobs:
        print(f"Scoring {j['title']} @ {j['company']}...")
        prompt = f"Score this job 0-100 for fit. Return JSON only: {{\"score\": int, \"rationale\": \"1 sentence\"}}\n\nCANDIDATE: {yaml.dump(profile)}\n\nJOB: {j['description']}"
        try:
            r = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            text = r.text.strip().removeprefix("```json").removesuffix("```").strip()
            data = json.loads(text)
            new_status = "SCORED" if data["score"] >= 70 else "REJECTED"
            update_status(con, j["job_id"], new_status, score=data["score"], rationale=data["rationale"])
            print(f" -> Score: {data['score']} ({new_status})")
        except Exception as e:
            print(f" -> Failed to parse: {e}")