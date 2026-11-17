import json, os, time
from groq import Groq
from db import get_db, update_status

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Hardcoded profile
profile = {"name": "Ayush Saraswat", "skills": ["Java", "Python", "Spring Boot"]}

def draft_for_scored():
    con = get_db()
    jobs = con.execute("SELECT * FROM applications WHERE status='SCORED'").fetchall()
    
    for j in jobs:
        print(f"Drafting answers for {j['company']}...")
        q = "Why are you interested in this role?"
        prompt = f"Answer this question using ONLY the facts in this profile. 120 words max. No cliches.\nQuestion: {q}\nCompany: {j['company']}\nProfile: {json.dumps(profile)}"
        
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
            )
            drafts = [{"question": q, "answer": chat_completion.choices[0].message.content.strip()}]
            update_status(con, j["job_id"], "DRAFTED", draft_answers=json.dumps(drafts))
            print(" -> Drafted.")
        except Exception as e:
            print(f" -> Failed: {e}")
        time.sleep(1)
