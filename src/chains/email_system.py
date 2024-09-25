import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText 
from email.header import decode_header
import email
import imaplib
from dotenv import load_dotenv

load_dotenv()

class EmailSystem:

    def __init__(self):
        self.SENDER_EMAIL_ID = os.getenv("EMAIL_USER")
        self.SENDER_EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
        self.SMTP_SERVER = os.getenv("SMTP_SERVER")

    def send_email(self, email_id : str, subject: str, message: str) -> str:

        if not all([email_id, subject, message]):
            return "Missing one or more required fields: email, subject, message"
                    
        msg = MIMEMultipart()
        msg['From'] = self.SENDER_EMAIL_ID
        msg['To'] = email_id
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        server = smtplib.SMTP(self.SMTP_SERVER, 587)
        server.starttls()
        server.login(self.SENDER_EMAIL_ID, self.SENDER_EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        return "Email sent successfully!"
    
    def check_inbox(self):
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(self.SENDER_EMAIL_ID, self.SENDER_EMAIL_PASSWORD)
        mail.select("inbox")
        
        _, message_numbers_raw = mail.search(None, 'UNSEEN')
        message_numbers = message_numbers_raw[0].split()
        
        if not message_numbers:
            return None

        for num in message_numbers:
            _, msg_data = mail.fetch(num, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])
            subject = decode_header(msg["subject"])[0][0]
            sender = msg.get("From")
            
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        return subject, sender, body
            else:
                body = msg.get_payload(decode=True).decode()
                return subject, sender, body

        return None