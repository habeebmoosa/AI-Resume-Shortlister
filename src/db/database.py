import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DATABASE_HOST_NAME"),
            user=os.getenv("DATABASE_USERNAME"),
            passwd=os.getenv("DATABASE_PASSWORD"),
            database=os.getenv("DATABASE_NAME")
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    
    return connection

def insert_candidate(connection, name, email, resume_link, linkedin_profile, job_id):
    cursor = connection.cursor()
    query = """
    INSERT INTO shortlisted_candidates (name, email, resume_link, linkedin_profile, job_id)
    VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(query, (name, email, resume_link, linkedin_profile, job_id))
    connection.commit()
    print(f"Candidate {name} inserted successfully")


def close_connection(connection):
    if connection.is_connected():
        connection.close()
        print("MySQL connection closed successfully")
    else:
        print("Connection is already closed")
