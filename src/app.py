from fastapi import FastAPI, UploadFile, File
import pandas as pd
import os
from pydantic import BaseModel

from src.utils.constants import UPLOAD_DIR
from src.process_user_info import process_excel_file, extract_resume_details
from src.ai_tools.resume_shortlist_model import shortlist_resumes
from src.db.database import create_connection, insert_candidate, close_connection

app = FastAPI()

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
    df = process_excel_file(job_data.filename)
    candidates_resume_data = extract_resume_details(df)
    shortlisted_emails = shortlist_resumes(candidates_resume_data, 
                                           job_data.job_description, 
                                           job_data.shortlist_count)
    
    for index, row in df.iterrows():
        email = row.get("Email")

        if email in shortlisted_emails:
            name = row.get("Name")
            resume = row.get("Google Drive Resume URL")
            linkedin_profile = row.get("Linkedin Profile URL")

            conn = create_connection()
            insert_candidate(conn, name, email, resume, linkedin_profile, job_data.job_id)
            close_connection(conn)

    return shortlisted_emails