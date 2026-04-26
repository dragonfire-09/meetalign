import sqlite3

DB_NAME = "meetalign.db"


def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS availability (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        email TEXT,
        role TEXT NOT NULL,
        date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def add_availability(meeting_id, name, email, role, date, start_time, end_time):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO availability 
    (meeting_id, name, email, role, date, start_time, end_time)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        meeting_id,
        name,
        email,
        role,
        str(date),
        str(start_time),
        str(end_time)
    ))

    conn.commit()
    conn.close()


def get_availability(meeting_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT name, email, role, date, start_time, end_time
    FROM availability
    WHERE meeting_id = ?
    """, (meeting_id,))

    rows = cur.fetchall()
    conn.close()
    return rows
