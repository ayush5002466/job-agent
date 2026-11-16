import discover, score, answer
import subprocess
import time
from db import get_db, update_status

def auto_approve():
    con = get_db()
    jobs = con.execute("SELECT * FROM applications WHERE status='DRAFTED'").fetchall()
    for job in jobs:
        if job['score'] >= 40: 
            update_status(con, job['job_id'], 'AWAITING_APPROVAL')
            print(f"✅ Auto-approved {job['company']}")

def run_application_engine():
    con = get_db()
    job = con.execute("SELECT * FROM applications WHERE status='AWAITING_APPROVAL' LIMIT 1").fetchone()
    
    if job:
        print(f"\n🚀 Launching Form Filler for {job['company']}...")
        subprocess.run(["python3", "submit_universal.py"])
    else:
        print("💤 No jobs ready to apply to.")

if __name__ == "__main__":
    for cycle in range(3): # Run 3 times per workflow
        print(f"\n🔄 Starting cycle {cycle + 1}...")
        score.score_pending()
        answer.draft_for_scored()
        auto_approve()
        run_application_engine()
        print(f"✅ Cycle {cycle + 1} done. Sleeping 5s...")
        time.sleep(5)
    print("🏁 All cycles complete. Exiting.")
