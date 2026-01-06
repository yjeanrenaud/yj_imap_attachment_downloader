#!./venv/bin/python3
import imaplib
import email
from email.header import decode_header
import os
import re

# ================== CONFIG ==================
IMAP_SERVER = "imap.example.com"
EMAIL_ACCOUNT = "someone@example.com"
EMAIL_PASSWORD = "secret" ## it's adviceable to use app passwords for Gmail or Hotmail. for other auth mechanisms, please adapt mail.login()
IMAP_FOLDER = "INBOX" ## the name of the folder to download.
# find the folder names by running python3 cli and paste everything above plus this: 
# mail = imaplib.IMAP4_SSL(IMAP_SERVER)
# mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
# mail.select(IMAP_FOLDER) # or ommit this line to see all IMAP folders of that mailbox
# status, folders = mail.list()
# for f in folders:
#     print(f.decode())
#
# ============================================
def imap_folder_to_path(folder: str) -> str:
    # Remove surrounding quotes if present
    folder = folder.strip('"')

    # Normalize separators (just in case)
    folder = folder.replace("\\", "/")

    # Prevent path traversal
    folder = re.sub(r"\.\.+", "", folder)
return os.path.join(".", folder)
DOWNLOAD_DIR = imap_folder_to_path(IMAP_FOLDER)

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def decode_filename(filename):
    if not filename:
        return None
    decoded, encoding = decode_header(filename)[0]
    if isinstance(decoded, bytes):
        return decoded.decode(encoding or "utf-8", errors="ignore")
    return decoded

# Connect to IMAP
mail = imaplib.IMAP4_SSL(IMAP_SERVER)
mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
mail.select(IMAP_FOLDER)
status, data = mail.select(IMAP_FOLDER)
if status != "OK":
    raise RuntimeError(f"Failed to select mailbox {IMAP_FOLDER}: {data}")

# Search all messages
status, messages = mail.search(None, "ALL")
email_ids = messages[0].split()

print(f"Found {len(email_ids)} messages")

import imaplib

def safe_fetch(mail, email_id):
    try:
        return mail.fetch(email_id, "(RFC822)")
    except imaplib.IMAP4.abort:
        print("IMAP connection lost, reconnecting...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(USERNAME, PASSWORD)
        mail.select("INBOX")
        return mail.fetch(email_id, "(RFC822)")


for email_id in email_ids:
    #status, msg_data = mail.fetch(email_id, "(RFC822)")
    status, msg_data = safe_fetch(mail, email_id)
    raw_email = msg_data[0][1]
    msg = email.message_from_bytes(raw_email)

    for part in msg.walk():
        if part.get_content_disposition() != "attachment":
            continue

        filename = decode_filename(part.get_filename())
        if not filename:
            continue
            
        if filename.lower().endswith(".pdf"):
            filepath = os.path.join(DOWNLOAD_DIR, filename)

            # Avoid overwriting
            base, ext = os.path.splitext(filepath)
            counter = 1
            while os.path.exists(filepath):
                filepath = f"{base}_{counter}{ext}"
                counter += 1

            with open(filepath, "wb") as f:
                f.write(part.get_payload(decode=True))

            print(f"Downloaded: {filepath}")

mail.logout()
