import os
import pandas as pd
import requests
from io import BytesIO
from pypdf import PdfReader

from src.utils.constants import UPLOAD_DIR

def extract_resume_details(df):
    resume_texts = {}

    for index, row in df.iterrows():
        email = row.get('Email')
        resume_url = row.get('Google Drive Resume URL')
        
        file_id = extract_file_id_of_google_drive_pdf(resume_url)

        if file_id:
            download_url = f'https://drive.google.com/uc?export=download&id={file_id}'

            try:
                # Fetch the PDF file from the download link
                response = requests.get(download_url)
                if response.status_code == 200:
                    # Read the PDF content in-memory
                    pdf_content = BytesIO(response.content)

                    # Extract text from the PDFs
                    reader = PdfReader(pdf_content)
                    text = ""
                    for page_num in range(len(reader.pages)):
                        page = reader.pages[page_num]
                        text += page.extract_text()

                    resume_texts[email] = text
                else:
                    continue
            except Exception as e:
                continue
        else:
            continue

    return resume_texts


def extract_file_id_of_google_drive_pdf(url):
    if "drive.google.com" in url and "/d/" in url:
        try:
            return url.split("/d/")[1].split("/")[0]
        except IndexError:
            return None
    return None
    


def process_excel_file(filename):
    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        return {
            "error":"File not found"
        }
    
    df = pd.read_excel(file_path)
    return df
    # resume_texts = extract_resume_details(df)

    # return resume_texts

