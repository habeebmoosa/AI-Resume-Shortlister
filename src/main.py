from fastapi import FastAPI, UploadFile, File
import pandas as pd
import os

from src.process_user_info import process_excel_file

UPLOAD_DIR = "uploads"

app = FastAPI()

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@app.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    if file is None:
        return {"message": "No file uploaded"}
    
    file_location = f"{UPLOAD_DIR}/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(file.file.read())

    df = process_excel_file(file.filename)

    return {"message": "File uploaded successfully", "filename": file.filename, "data": df.head().to_dict()}

@app.get("/read")
async def read_excel(filename = "resumes.xlsx"):
    df = process_excel_file(filename)
    # return {"message": "File uploaded successfully", "filename": filename, "data": df.head().to_dict()}
    return df