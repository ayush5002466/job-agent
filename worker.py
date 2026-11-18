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
        print(f"\n🚀 Applying to {job['company']}...")
        try:
            subprocess.run(["python3", "submit_universal.py"], timeout=240)
        except Exception as e:
            print(f"Subprocess error: {e}")

if __name__ == "__main__":
    for cycle in range(3):
        print(f"\n🔄 Cycle {cycle + 1}/3")
        discover.discover()           # <--- THIS WAS MISSING
        score.score_pending()
        answer.draft_for_scored()
        auto_approve()
        run_application_engine()
        time.sleep(3)
    print("🏁 Done.")
