import json, os, yaml
from google import genai
from db import get_db, update_status

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
profile = yaml.safe_load(open("profile.yaml"))

def draft_for_scored():
    con = get_db()
    jobs = con.execute("SELECT * FROM applications WHERE status='SCORED'").fetchall()
    for j in jobs:
        print(f"Drafting answers for {j['company']}...")
        q = "Why are you interested in this role?"
        prompt = f"Answer this question using ONLY the facts in this profile. 120 words max. No cliches.\nQuestion: {q}\nCompany: {j['company']}\nProfile: {yaml.dump(profile)}"
        try:
            r = client.models.generate_content(model="gemini-3.8-flash", contents=prompt)
            drafts = [{"question": q, "answer": r.text.strip()}]
            update_status(con, j["job_id"], "DRAFTED", draft_answers=json.dumps(drafts))
            print(" -> Drafted.")
        except Exception as e:
            print(f" -> Failed: {e}")
