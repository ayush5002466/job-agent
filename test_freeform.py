import json, os, yaml
from google import genai
from db import get_db, update_status

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
profile = yaml.safe_load(open("profile.yaml"))

questions = [
    "Please provide a brief summary highlighting your top two academic or professional accomplishments/projects.",
    "Why do you want to work at Freeform?",
    "Why did you want to become an engineer in your respective discipline?",
    "What unique skills, abilities, or experience would you bring to the role?"
]

con = get_db()
drafts = []

print("Asking Gemini to draft answers based on your resume...")
for q in questions:
    prompt = f"Answer this question using ONLY the facts in this profile. Max 100 words. No cliches. Write in first person.\nQuestion: {q}\nJob: Freeform Software Engineering Intern (3D printing, hardware/software integration)\nProfile: {yaml.dump(profile)}"
    r = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
    drafts.append({"question": q, "answer": r.text.strip()})
    print(f"✅ Drafted: {q[:40]}...")

# Insert into DB (Using a placeholder URL for now)
job_url = "PASTE_PUBLIC_URL_HERE" 

con.execute(
    """INSERT OR REPLACE INTO applications (job_id, company, title, url, score, rationale, draft_answers, status) 
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
    ('freeform_1', 'Freeform', 'Software Engineering Intern (Summer 2027)', job_url, 90, 'Great match for backend and Python skills.', json.dumps(drafts), 'AWAITING_APPROVAL')
)
con.commit()
print("\n✅ Job inserted into database with drafted answers!")
