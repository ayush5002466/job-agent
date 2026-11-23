import json, os, time
from groq import Groq
from db import get_db, update_status

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
profile = {"name": "Ayush Saraswat", "skills": ["Java", "Python", "Spring Boot"]}

def draft_for_scored():
    con = get_db()
    jobs = con.execute("SELECT * FROM applications WHERE status='SCORED' LIMIT 5").fetchall()
    print(f"Found {len(jobs)} SCORED jobs to draft answers for.")
    
    for j in jobs:
        try:
            print(f"Drafting answers for {j['title']} @ {j['company']}...")
            
            # Truncate description to save tokens
            desc = (j['description'] or "")[:2000]
            
            prompt = f"""Write a short, professional cover letter paragraph (max 100 words) for this job.
CANDIDATE: {json.dumps(profile)}
JOB TITLE: {j['title']}
JOB DESCRIPTION: {desc}

Return JSON only: {{"cover_letter": "your text here"}}"""
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="openai/gpt-oss-20b",  # NEW MODEL
                response_format={"type": "json_object"}
            )
            
            text = chat_completion.choices[0].message.content
            data = json.loads(text)
            
            # Format it as a list of Q&A for the dashboard
            draft_answers = json.dumps([{
                "question": "Cover Letter / Additional Information",
                "answer": data.get("cover_letter", "Dear Hiring Manager, I am very interested in this role.")
            }])
            
            update_status(con, j["job_id"], "DRAFTED", draft_answers=draft_answers)
            print(f" -> Successfully drafted for {j['company']}")
            
        except Exception as e:
            print(f" -> Error drafting for {j['title']}: {e}")
            # We don't mark as ERROR so it can retry next time, but we log it.
        
        time.sleep(3) # Avoid rate limits
