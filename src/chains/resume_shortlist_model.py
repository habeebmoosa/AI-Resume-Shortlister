from dotenv import load_dotenv
import google.generativeai as genai
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAI
import json
import re
import requests
import os

from src.utils.constants import REGEX_PARSE

load_dotenv()

class ShortlistResume:
    def __init__(self):
        self.FLOWISE_RESUME_SHORTLIST = os.getenv("FLOWISE_RESUME_SHORTLIST")

    def shortlist_resumes(self, candidates_data, job_description, shortlist_count):
        promptValues = {
                "job_description": job_description,
                "shortlist_count": shortlist_count,
                "candidates": candidates_data
        }

        payload = {
        "question": promptValues
        }

        response = requests.post(self.FLOWISE_RESUME_SHORTLIST, json=payload)
        result = response.json()
        print(result['text'])

        # email_list = json.loads(result['text'])

        return result['text']