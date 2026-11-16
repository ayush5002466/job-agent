import imaplib
import email
import re
import time
import os

def get_otp():
    user = os.getenv("GMAIL_USER")
    password = os.getenv("GMAIL_APP_PASSWORD")
    if not user or not password:
        print("Gmail credentials not found.")
        return None

    print("  -> Waiting 10 seconds for OTP email to arrive...")
    time.sleep(10)

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, password)
        mail.select("inbox")

        # Search for recent emails from Greenhouse
        result, data = mail.search(None, '(FROM "greenhouse.io")')
        mail_ids = data[0].split()
        if not mail_ids:
            print("  -> No Greenhouse emails found.")
            return None

        latest_email_id = mail_ids[-1]
        result, data = mail.fetch(latest_email_id, "(RFC822)")
        raw_email = data[0][1]
        email_message = email.message_from_bytes(raw_email)

        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = email_message.get_payload(decode=True).decode()

        # Extract 8-character code (alphanumeric)
        match = re.search(r'\b[A-Z0-9]{8}\b', body)
        if match:
            return match.group(0)
        return None
    except Exception as e:
        print(f"  -> Gmail error: {e}")
        return None
