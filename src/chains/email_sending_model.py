from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate

import os
import re
from datetime import datetime

from src.db.database import DatabaseSystem
from src.chains.email_system import EmailSystem

db = DatabaseSystem()
emailSystem = EmailSystem()

load_dotenv()

class EmailChainSystem:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

    def email_sending_agent(self, name:str, email:str, job_id:int):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system","You are a helpfull assistant that generates congratulation email for shortlisted candidate and ask for interview sheduel date."),
                ("human", "Generate only message of mail (no subject) for {name} for shortlisting in the companay {company_name} for the job id {job_id}. Available dates for interview {dates}, and {timing}")
            ]
        )
        
        chain = prompt_template | self.llm | StrOutputParser()

        response = chain.invoke({"name": name, "company_name":"AgentProd Team", "job_id":job_id, "dates":"15 Oct 2024 to 18 Oct 2024", "timing":"10 AM to 4PM"})
        emailSystem.send_email(email, "Congrats for shortlisting. Take further actions.", response)
        return response


    def read_and_schedule_interview(self, email_data):
        subject, sender_email, email_body = email_data

        just_email = re.search(r'<([^>]+)>', sender_email).group(1)
        print(just_email)

        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "You are an email reader. You need to read the email and give the candidate's selected interview date only in this format and numbers only: Year, Month, Day"),
                ("human", "Email: {email_body}")
            ]
        )

        chain = prompt_template | self.llm | StrOutputParser()
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
            self.reply_email_with_meeting_link(name, email, job_id)
        else:
            print("Candidate not found in the database.")

        db.close_connection(conn)

        return f"Interview scheduled on {interview_date}"
    

    def reply_email_with_meeting_link(self, name, email, job_id):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system","You are a helpfull assistant that generates interview shedule meeting email with meeting link"),
                ("human", "Generate only message of mail (no subject) for {name} for scheduling interview in the companay {company_name} for the job id {job_id}.The meeting link is {meeting_link}")
            ]
        )

        chain = prompt_template | self.llm | StrOutputParser()

        response = chain.invoke({"name": name, "company_name":"AgentProd Team", "job_id":job_id, "meeting_link":os.getenv("GOOGLE_MEET_LINK")})
        emailSystem.send_email(email, "You go for next step. Interview is scheduled.", response)
        return response


    def process_incoming_email(self):
        email_data = emailSystem.check_inbox()
        if email_data:
            return self.read_and_schedule_interview(email_data)
