import time
import discover, score, answer
from db import get_db, update_status

def auto_approve():
    con = get_db()
    jobs = con.execute("SELECT * FROM applications WHERE status='DRAFTED'").fetchall()
    for job in jobs:
        if job['score'] >= 80:
            update_status(con, job['job_id'], 'AWAITING_APPROVAL')
            print(f"✅ Auto-approved {job['company']}")

def loop():
    while True:
        try:
            print("\n🔄 Starting cycle...")
            discover.discover()
            score.score_pending()
            answer.draft_for_scored()
            auto_approve()
            print("💤 Cycle done. Sleeping for 30 minutes...")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1800)

if __name__ == "__main__":
    loop()
