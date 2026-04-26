import sqlite3
import uuid

DATABASE_FILE = "meetalign.db"


def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_code TEXT UNIQUE,
            title TEXT,
            status TEXT DEFAULT 'active',
            confirmed_date TEXT DEFAULT '',
            confirmed_start TEXT DEFAULT '',
            confirmed_end TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_code TEXT,
            name TEXT,
            email TEXT,
            role TEXT,
            date TEXT,
            start_time TEXT,
            end_time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS meeting_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_code TEXT,
            action TEXT,
            detail TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def create_meeting(title):
    meeting_code = uuid.uuid4().hex[:8].upper()
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO meetings (meeting_code, title) VALUES (?, ?)",
        (meeting_code, title)
    )
    c.execute(
        "INSERT INTO meeting_history (meeting_code, action, detail) VALUES (?, ?, ?)",
        (meeting_code, "created", f"Meeting created: {title}")
    )
    conn.commit()
    conn.close()
    return meeting_code


def get_meeting(meeting_code):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        "SELECT id, title, status, confirmed_date, confirmed_start, confirmed_end FROM meetings WHERE meeting_code = ?",
        (meeting_code,)
    )
    row = c.fetchone()
    conn.close()
    return row


def add_availability(meeting_code, name, email, role, date, start_time, end_time):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        """INSERT INTO availability (meeting_code, name, email, role, date, start_time, end_time)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (meeting_code, name, email, role,
         date if isinstance(date, str) else date.strftime("%Y-%m-%d"),
         start_time if isinstance(start_time, str) else start_time.strftime("%H:%M"),
         end_time if isinstance(end_time, str) else end_time.strftime("%H:%M"))
    )
    c.execute(
        "INSERT INTO meeting_history (meeting_code, action, detail) VALUES (?, ?, ?)",
        (meeting_code, "availability_added", f"{name} ({role}) added availability for {date}")
    )
    conn.commit()
    conn.close()


def get_availability(meeting_code):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        "SELECT name, email, role, date, start_time, end_time FROM availability WHERE meeting_code = ? ORDER BY date, start_time",
        (meeting_code,)
    )
    rows = c.fetchall()
    conn.close()
    return rows


def cancel_meeting(meeting_code):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        "UPDATE meetings SET status = 'cancelled' WHERE meeting_code = ?",
        (meeting_code,)
    )
    c.execute(
        "INSERT INTO meeting_history (meeting_code, action, detail) VALUES (?, ?, ?)",
        (meeting_code, "cancelled", "Meeting cancelled")
    )
    conn.commit()
    conn.close()


def archive_meeting(meeting_code):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        "UPDATE meetings SET status = 'archived' WHERE meeting_code = ?",
        (meeting_code,)
    )
    c.execute(
        "INSERT INTO meeting_history (meeting_code, action, detail) VALUES (?, ?, ?)",
        (meeting_code, "archived", "Meeting archived")
    )
    conn.commit()
    conn.close()


def restore_meeting(meeting_code):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        "UPDATE meetings SET status = 'active' WHERE meeting_code = ?",
        (meeting_code,)
    )
    c.execute(
        "INSERT INTO meeting_history (meeting_code, action, detail) VALUES (?, ?, ?)",
        (meeting_code, "restored", "Meeting restored to active")
    )
    conn.commit()
    conn.close()


def confirm_meeting_slot(meeting_code, date, start, end):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        """UPDATE meetings
           SET status = 'confirmed', confirmed_date = ?, confirmed_start = ?, confirmed_end = ?
           WHERE meeting_code = ?""",
        (date, start, end, meeting_code)
    )
    c.execute(
        "INSERT INTO meeting_history (meeting_code, action, detail) VALUES (?, ?, ?)",
        (meeting_code, "confirmed", f"Confirmed: {date} {start}-{end}")
    )
    conn.commit()
    conn.close()


def get_meeting_history(meeting_code):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        "SELECT action, detail, created_at FROM meeting_history WHERE meeting_code = ? ORDER BY created_at DESC",
        (meeting_code,)
    )
    rows = c.fetchall()
    conn.close()
    return rows


def get_all_meetings():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        "SELECT meeting_code, title, status, created_at FROM meetings ORDER BY created_at DESC"
    )
    rows = c.fetchall()
    conn.close()
    return rows
