import json, os, yaml, time
from google import genai
from db import get_db, update_status

# Automatically find all keys
KEYS = [v for k, v in os.environ.items() if k.startswith("GEMINI_API_KEY") and v]
current_key_index = 0
client = genai.Client(api_key=KEYS[current_key_index])
profile = yaml.safe_load(open("profile.yaml"))

def draft_for_scored():
    global current_key_index, client
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
            if "429" in str(e) or "503" in str(e):
                current_key_index += 1
                if current_key_index >= len(KEYS):
                    print("\n🚨 ALL API KEYS EXHAUSTED. Stopping drafting.\n")
                    break
                print(f"\n🔄 Limit hit. Rotating to API Key #{current_key_index + 1}...\n")
                client = genai.Client(api_key=KEYS[current_key_index])
                time.sleep(2)
            else:
                print(f" -> Failed: {e}")
        time.sleep(3)
