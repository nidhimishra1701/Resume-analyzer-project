import mysql.connector

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="soni@123",
        database="resume_analyzer"
    )

def insert_data(name, email, resume_text, score):
    conn = connect_db()
    cursor = conn.cursor()
    query = """
    INSERT INTO resumes (name, email, resume_text, score)
    VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (name, email, resume_text, score))
    conn.commit()
    conn.close()