import sqlite3
import uuid
from datetime import datetime

DB_NAME = "meetalign_v2.db"


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
        created_at TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        archived_at TEXT,
        cancel_reason TEXT
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

    # Migration support for old database
    existing_columns = [
        row[1] for row in cur.execute("PRAGMA table_info(meetings)").fetchall()
    ]

    if "status" not in existing_columns:
        cur.execute("ALTER TABLE meetings ADD COLUMN status TEXT DEFAULT 'active'")

    if "archived_at" not in existing_columns:
        cur.execute("ALTER TABLE meetings ADD COLUMN archived_at TEXT")

    if "cancel_reason" not in existing_columns:
        cur.execute("ALTER TABLE meetings ADD COLUMN cancel_reason TEXT")

    conn.commit()
    conn.close()


def create_meeting(title):
    conn = get_connection()
    cur = conn.cursor()

    meeting_code = str(uuid.uuid4())[:8].upper()

    cur.execute("""
    INSERT INTO meetings (meeting_code, title, created_at, status)
    VALUES (?, ?, ?, ?)
    """, (
        meeting_code,
        title,
        datetime.now().isoformat(),
        "active"
    ))

    conn.commit()
    conn.close()

    return meeting_code


def get_meeting(meeting_code):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT meeting_code, title, created_at, status, archived_at, cancel_reason
    FROM meetings
    WHERE meeting_code = ?
    """, (meeting_code,))

    row = cur.fetchone()
    conn.close()

    return row


def cancel_meeting(meeting_code, reason=""):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    UPDATE meetings
    SET status = 'cancelled',
        archived_at = ?,
        cancel_reason = ?
    WHERE meeting_code = ?
    """, (
        datetime.now().isoformat(),
        reason,
        meeting_code
    ))

    conn.commit()
    conn.close()


def restore_meeting(meeting_code):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    UPDATE meetings
    SET status = 'active',
        archived_at = NULL,
        cancel_reason = NULL
    WHERE meeting_code = ?
    """, (meeting_code,))

    conn.commit()
    conn.close()


def get_archived_meetings():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT meeting_code, title, created_at, archived_at, cancel_reason
    FROM meetings
    WHERE status = 'cancelled'
    ORDER BY archived_at DESC
    """)

    rows = cur.fetchall()
    conn.close()

    return rows


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
