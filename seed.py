import sqlite3
import json

con = sqlite3.connect('data/applications.db')

draft = [
    {
        "question": "Why are you interested in Hadrian?",
        "answer": "I am excited by Hadrian's approach to automated manufacturing. My background in building scalable backend systems aligns perfectly with your need for robust infrastructure."
    },
    {
        "question": "Tell us about a project you are most proud of.",
        "answer": "I built a real-time chat app using FastAPI and Redis, which successfully handled 200 concurrent users with a 50ms p99 latency."
    }
]

con.execute(
    """INSERT INTO applications (job_id, company, title, score, rationale, draft_answers, status) 
       VALUES (?, ?, ?, ?, ?, ?, ?)""",
    ('test_123', 'Hadrian', 'Software Engineer Intern', 95, 'Great match for your backend skills.', json.dumps(draft), 'DRAFTED')
)
con.commit()
print("✅ Test job added to database!")
