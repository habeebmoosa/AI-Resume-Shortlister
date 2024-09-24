from dotenv import load_dotenv
import google.generativeai as genai
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAI
import json
import re

from src.utils.constants import REGEX_PARSE, EXAMPLE_DATA_OF_CANDIDATES

load_dotenv()

def shortlist_resumes(candidates_data, job_description, shortlist_count):
    
    llm = GoogleGenerativeAI(model="gemini-1.5-flash")

    shortlist_template = """
    You are a hiring manager. You have received the resumes of some candidates as input. You want to shortlist {shortlist_count} candidates at max based on job description {job_description}.
    Please go through their resumes and list only their email addresses that should be shortlisted based on the requirements. Do not include any other information, just their emails in JSON format.
    Input: {candidates}
    """

    prompt_template = PromptTemplate.from_template(shortlist_template)

    chain = prompt_template | llm

    result = chain.invoke(
        {
            "candidates":candidates_data,
            "job_description":job_description,
            "shortlist_count": shortlist_count,
            
        }
    )

    match = re.search(REGEX_PARSE, result)

    if match:
        json_data = match.group(1)
        shortlisted_emails = json.loads(json_data)
        email_list = list(shortlisted_emails.keys())
    else:
        return {"message":"Model is not working or json is not parsing."}
    
    return email_list