# Fix for SQLite version on Streamlit Cloud
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import json
from db import get_db

# Set up the page layout
st.set_page_config(page_title="Job Agent Dashboard", page_icon="🤖", layout="wide")

st.title("🤖 AI Job Agent Dashboard")
st.write("Here are the jobs the agent has drafted applications for, waiting for your review.")

try:
    con = get_db()
    # Look for both DRAFTED and AWAITING_APPROVAL statuses
    jobs = con.execute("SELECT * FROM applications WHERE status IN ('DRAFTED', 'AWAITING_APPROVAL')").fetchall()
    
    if not jobs:
        st.info("No drafts found in the database yet. The agent is still working!")
    else:
        for j in jobs:
            # Create a dropdown for each job
            with st.expander(f"🏢 {j['title']} @ {j['company']} — Score: {j['score']}"):
                st.markdown(f"**Rationale:** {j['rationale']}")
                st.markdown(f"**URL:** [Apply Here]({j['url']})")
                st.divider()
                
                st.write("### 📝 Drafted Answers")
                answers = json.loads(j["draft_answers"] or "[]")
                if not answers:
                    st.write("No answers drafted yet.")
                
                for a in answers:
                    st.write(f"**❓ {a['question']}**")
                    st.info(a['answer'])

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
