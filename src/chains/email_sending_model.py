from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate

import os
import re
from datetime import datetime
import requests
import httpx
import asyncio

from src.db.database import DatabaseSystem
from src.chains.email_system import EmailSystem

db = DatabaseSystem()
emailSystem = EmailSystem()

load_dotenv()

class EmailChainSystem:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
        self.FLOWISE_SEND_EMAIL = os.getenv("FLOWISE_SEND_EMAIL")
        self.FLOWISE_EMAIL_RESPONDER = os.getenv("FLOWISE_EMAIL_RESPONDER")

    def email_sending_agent(self, name:str, email:str, job_id:int):
        promptValues = {
        "name":name,
        "company_name":"AgentProd Team",
        "job_id":job_id,
        "dates":"15 Oct 2024 to 18 Oct 2024"
        }

        payload = {
            "question": promptValues
        }

        response = requests.post(self.FLOWISE_SEND_EMAIL, json=payload)
        result = response.json()

        emailSystem.send_email(email, "Congrats for shortlisting. Take further actions.", result['text'])
        return response


    async def read_and_schedule_interview(self, email_data):
        subject, sender_email, email_body = email_data

        just_email = re.search(r'<([^>]+)>', sender_email).group(1)
        print(just_email)

        conn = db.create_connection()
        candidate_data = db.read_candidate(conn, just_email)  # Ensure this is async

        if candidate_data:
            id, name, email, _, _, job_id = candidate_data
            print(f"Interview scheduled for {name}")
            await self.reply_email_with_meeting_link(name, email, job_id, email_body)
        else:
            print("Candidate not found in the database.")

        db.close_connection(conn)

        return f"Interview scheduled confirmed for {name}"
    

    async def reply_email_with_meeting_link(self, name, email, job_id, email_body):
        input_data = {
            "email": email_body,
            "name": name,
            "company_name": "AgentProd Team"
        }

        payload = {"question": input_data}

        retries = 3
        for attempt in range(retries):
            try:
                response = requests.post(self.FLOWISE_EMAIL_RESPONDER, json=payload, timeout=30.0)
                result = response.json()
                break
            except httpx.ReadTimeout:
                if attempt < retries - 1:
                    await asyncio.sleep(2) 
                else:
                    raise
        
        await emailSystem.send_email(email, "You go for next step. Interview is scheduled.", result['text'])
        return response

    async def process_incoming_email(self):
        email_data = await emailSystem.check_inbox()
        if email_data:
            return await self.read_and_schedule_interview(email_data)
