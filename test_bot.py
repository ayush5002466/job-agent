import asyncio
import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application
from db import get_db

# REPLACE THE STRING BELOW WITH YOUR ACTUAL TOKEN
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
CHAT_ID = 1250255302  # Your ID

async def main():
    con = get_db()
    job = con.execute("SELECT * FROM applications WHERE status='DRAFTED' LIMIT 1").fetchone()
    
    if not job:
        print("No jobs found in database!")
        return

    answers = json.loads(job["draft_answers"])
    body = f"*{job['title']}* @ {job['company']}\nScore {job['score']}: {job['rationale']}\n\n"
    for a in answers:
        body += f"*Q:* {a['question']}\n{a['answer']}\n\n"

    kb = [[
        InlineKeyboardButton("✅ Approve", callback_data="approve"),
        InlineKeyboardButton("❌ Skip", callback_data="skip"),
    ]]

    app = Application.builder().token(BOT_TOKEN).build()
    await app.bot.send_message(
        chat_id=CHAT_ID, 
        text=body, 
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode="Markdown"
    )
    print("Message sent! Check your Telegram.")

if __name__ == "__main__":
    asyncio.run(main())
