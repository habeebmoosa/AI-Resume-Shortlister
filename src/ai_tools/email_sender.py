from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText 
from email.header import decode_header
import email
import imaplib
import re
from datetime import datetime

from src.db.database import DatabaseSystem

db = DatabaseSystem()

load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
memory = ConversationBufferMemory()

SENDER_EMAIL_ID = os.getenv("EMAIL_USER")
SENDER_EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")

def send_email(email_id : str, subject: str, message: str) -> str:

    if not all([email_id, subject, message]):
        return "Missing one or more required fields: email, subject, message"
                
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL_ID
    msg['To'] = email_id
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    server = smtplib.SMTP(SMTP_SERVER, 587)
    server.starttls()
    server.login(SENDER_EMAIL_ID, SENDER_EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()

    return "Email sent successfully!"
    

def email_sending_agent(name:str, email:str, job_id:int):
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system","You are a helpfull assistant that generates congratulation email for shortlisted candidate and ask for interview sheduel date."),
            ("human", "Generate only message of mail (no subject) for {name} for shortlisting in the companay {company_name} for the job id {job_id}. Available dates for interview {dates}, and {timing}")
        ]
    )
     
    chain = prompt_template | llm | StrOutputParser()

    response = chain.invoke({"name": name, "company_name":"AgentProd Team", "job_id":job_id, "dates":"15 Oct 2024 to 18 Oct 2024", "timing":"10 AM to 4PM"})
    send_email(email, "Congrats for shortlisting. Take further actions.", response)
    return response


def check_inbox():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(SENDER_EMAIL_ID, SENDER_EMAIL_PASSWORD)
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


def read_and_schedule_interview(email_data):
    subject, sender_email, email_body = email_data

    just_email = re.search(r'<([^>]+)>', sender_email).group(1)
    print(just_email)

    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an email reader. You need to read the email and give the candidate's selected interview date only in this format and numbers only: Year, Month, Day"),
            ("human", "Email: {email_body}")
        ]
    )

    chain = prompt_template | llm | StrOutputParser()
    interview_date = chain.invoke({"email_body": email_body})

    cleaned_date_str = interview_date.replace("-", "").strip()
    date_obj = datetime.strptime(cleaned_date_str, "%Y, %m, %d")
    formatted_date = date_obj.strftime("%Y-%m-%d")
    print(formatted_date)
    
    conn = db.create_connection()
    candidate_data = db.read_candidate(conn, just_email)

    if candidate_data:
        id, name, email, _, _, job_id = candidate_data

        db.store_interview_data(conn, id, name, email, job_id, formatted_date)

        print(f"Interview scheduled for {name} on {interview_date}")
    else:
        print("Candidate not found in the database.")

    db.close_connection(conn)

    reply_email_with_meeting_link(name, email, job_id)

    return f"Interview scheduled on {interview_date}"

def process_incoming_email():
    email_data = check_inbox()
    if email_data:
        return read_and_schedule_interview(email_data)
    
def reply_email_with_meeting_link(name, email, job_id):
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system","You are a helpfull assistant that generates interview shedule meeting email with meeting link"),
            ("human", "Generate only message of mail (no subject) for {name} for scheduling interview in the companay {company_name} for the job id {job_id}.The meeting link is {meeting_link}")
        ]
    )

    chain = prompt_template | llm | StrOutputParser()

    response = chain.invoke({"name": name, "company_name":"AgentProd Team", "job_id":job_id, "meeting_link":os.getenv("GOOGLE_MEET_LINK")})
    send_email(email, "You go for next step. Interview is scheduled.", response)
    return response
