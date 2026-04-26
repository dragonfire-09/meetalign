import sqlite3
import uuid
from datetime import datetime

DB_NAME = "meetalign.db"


def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS availability (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_code TEXT NOT NULL,
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


def create_meeting(title):
    conn = get_connection()
    cur = conn.cursor()

    meeting_code = str(uuid.uuid4())[:8].upper()

    cur.execute("""
    INSERT INTO meetings (meeting_code, title, created_at)
    VALUES (?, ?, ?)
    """, (meeting_code, title, datetime.now().isoformat()))

    conn.commit()
    conn.close()

    return meeting_code


def get_meeting(meeting_code):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT meeting_code, title, created_at
    FROM meetings
    WHERE meeting_code = ?
    """, (meeting_code,))

    row = cur.fetchone()
    conn.close()
    return row


def add_availability(meeting_code, name, email, role, date, start_time, end_time):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO availability 
    (meeting_code, name, email, role, date, start_time, end_time)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        meeting_code,
        name,
        email,
        role,
        str(date),
        str(start_time),
        str(end_time)
    ))

    conn.commit()
    conn.close()


def get_availability(meeting_code):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT name, email, role, date, start_time, end_time
    FROM availability
    WHERE meeting_code = ?
    """, (meeting_code,))

    rows = cur.fetchall()
    conn.close()
    return rows
