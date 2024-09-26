from fastapi import FastAPI, UploadFile, File, BackgroundTasks
import os
from pydantic import BaseModel
import time
import pandas as pd
import asyncio

from src.utils.constants import UPLOAD_DIR
from src.process_xl.process_user_info import ProcessResume
from src.chains.resume_shortlist_model import ShortlistResume
from src.db.database import DatabaseSystem
from src.chains.email_sending_model import EmailChainSystem

app = FastAPI()

processResume = ProcessResume()
db = DatabaseSystem()
shortlistResume = ShortlistResume()
emailChainSystem = EmailChainSystem()

class JobData(BaseModel):
    job_description: str
    shortlist_count: int
    job_id: int
    filename: str


if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


@app.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    if file is None:
        return {"message": "No file uploaded"}
    
    file_location = f"{UPLOAD_DIR}/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(file.file.read())

    return {"message": "File uploaded successfully", "filename": file.filename}


@app.post("/shortlist")
async def read_excel(job_data: JobData):
    df = processResume.process_excel_file(job_data.filename)
    candidates_resume_data = processResume.extract_resume_details(df)
    shortlisted_emails = shortlistResume.shortlist_resumes(candidates_resume_data, 
                                           job_data.job_description, 
                                           job_data.shortlist_count)
    
    for index, row in df.iterrows():
        email = row.get("Email")

        if email in shortlisted_emails:
            name = row.get("Name")
            resume = row.get("Google Drive Resume URL")
            linkedin_profile = row.get("Linkedin Profile URL")

            conn = db.create_connection()
            db.insert_candidate(conn, name, email, resume, linkedin_profile, job_data.job_id)
            db.close_connection(conn)

            emailChainSystem.email_sending_agent(name, email, job_data.job_id)

    return shortlisted_emails

async def email_responder_task():
    while True:
        await emailChainSystem.process_incoming_email()
        await asyncio.sleep(30)

@app.get("/start-email-responder")
async def start_email_responder(background_tasks: BackgroundTasks):
    background_tasks.add_task(email_responder_task)
    return {"message": "Email responder started."}