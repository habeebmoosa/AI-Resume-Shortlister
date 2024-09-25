from fastapi import FastAPI, UploadFile, File
import os
from pydantic import BaseModel
import time
import pandas as pd

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

class InputUser(BaseModel):
    email: str
    job_id: int


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


@app.get("/readuser")
async def read_user(input_user: InputUser):
    conn = db.create_connection()
    data = db.read_candidate(conn, input_user.email)
    db.close_connection(conn)
    return data

@app.get("/emailresponder")
async def email_responder():
    while True:
        emailChainSystem.process_incoming_email()
        time.sleep(300)