import sqlite3

def create_connection():
    conn = sqlite3.connect('candidates.db')
    return conn

def create_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS candidates (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        email TEXT,
                        skills TEXT,
                        experience TEXT)''')
    conn.commit()
    conn.close()

def insert_candidate(name, email, skills, experience):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO candidates (name, email, skills, experience)
                      VALUES (?, ?, ?, ?)''', (name, email, skills, experience))
    conn.commit()
    conn.close()

def get_all_candidates():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates")
    candidates = cursor.fetchall()
    conn.close()
    return candidates
