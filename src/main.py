from fastapi import FastAPI, UploadFile, File
import pandas as pd
import os

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

    df = pd.read_excel(file_location)

    return {"message": "File uploaded successfully", "filename": file.filename, "data": df.head().to_dict()}