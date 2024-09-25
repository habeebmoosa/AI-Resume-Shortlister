import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

class DatabaseSystem:
    def __init__(self):
        self.host = os.getenv("DATABASE_HOST_NAME")
        self.user = os.getenv("DATABASE_USERNAME")
        self.password = os.getenv("DATABASE_PASSWORD")
        self.database = os.getenv("DATABASE_NAME")

    def create_connection(self):
        connection = None
        try:
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                passwd=self.password,
                database=self.database
            )
            print("Connection to MySQL DB successful")
        except Error as e:
            print(f"The error '{e}' occurred")
        
        return connection

    def insert_candidate(self, connection, name, email, resume_link, linkedin_profile, job_id):
        cursor = connection.cursor()
        query = """
        INSERT INTO shortlisted_candidates (name, email, resume_link, linkedin_profile, job_id)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, email, resume_link, linkedin_profile, job_id))
        connection.commit()
        print(f"Candidate {name} inserted successfully")


    def close_connection(self, connection):
        if connection.is_connected():
            connection.close()
            print("MySQL connection closed successfully")
        else:
            print("Connection is already closed")


    def read_candidate(self, connection, email, job_id):
        cursor = connection.cursor()
        query = """
        SELECT * FROM shortlisted_candidates WHERE email = %s OR job_id = %s
        """
        cursor.execute(query, (email, job_id))
        data = cursor.fetchone()
        connection.commit()
        return data
    
    
    def store_interview_data(self, connection, id, name, email, job_id, interview_date):
        cursor = connection.cursor()
        query = '''INSERT INTO interview_data (id, name, email, job_id, interview_date)
                   VALUES (%s, %s, %s, %s, %s)'''
        cursor.execute(query, (id, name, email, job_id, interview_date))
        connection.commit()
        print(f"Interview of {name} is scheduled")
