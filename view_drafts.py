from db import get_db
import json

def show_drafts():
    con = get_db()
    # Look for both DRAFTED and AWAITING_APPROVAL statuses
    jobs = con.execute("SELECT * FROM applications WHERE status IN ('DRAFTED', 'AWAITING_APPROVAL')").fetchall()
    
    if not jobs:
        print("No drafts found in the database.")
        return

    for j in jobs:
        print("\n" + "=" * 60)
        print(f"🏢 {j['title']} @ {j['company']}")
        print(f"⭐ Score: {j['score']} — {j['rationale']}")
        print(f"🔗 URL: {j['url']}")
        print("=" * 60)
        
        answers = json.loads(j["draft_answers"] or "[]")
        for a in answers:
            print(f"\n❓ Q: {a['question']}")
            print(f"💬 A: {a['answer']}")
        print("=" * 60 + "\n")

if __name__ == "__main__":
    show_drafts()
