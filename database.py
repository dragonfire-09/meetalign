import sqlite3
import uuid
from datetime import datetime

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
            meeting_link TEXT DEFAULT '',
            confirmed_date TEXT DEFAULT '',
            confirmed_start TEXT DEFAULT '',
            confirmed_end TEXT DEFAULT '',
            cancel_reason TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            archived_at TEXT DEFAULT ''
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

    # Migration: eski tablolara yeni sütun ekle
    c.execute("PRAGMA table_info(meetings)")
    cols = [r[1] for r in c.fetchall()]

    migrations = {
        "status": "TEXT DEFAULT 'active'",
        "meeting_link": "TEXT DEFAULT ''",
        "confirmed_date": "TEXT DEFAULT ''",
        "confirmed_start": "TEXT DEFAULT ''",
        "confirmed_end": "TEXT DEFAULT ''",
        "cancel_reason": "TEXT DEFAULT ''",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "archived_at": "TEXT DEFAULT ''"
    }

    for col, col_type in migrations.items():
        if col not in cols:
            try:
                c.execute(f"ALTER TABLE meetings ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass

    c.execute("PRAGMA table_info(availability)")
    av_cols = [r[1] for r in c.fetchall()]
    if "created_at" not in av_cols:
        try:
            c.execute("ALTER TABLE availability ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()


def create_meeting(title, meeting_link=""):
    code = uuid.uuid4().hex[:8].upper()
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO meetings (meeting_code, title, status, meeting_link) VALUES (?, ?, 'active', ?)",
        (code, title, meeting_link)
    )
    c.execute(
        "INSERT INTO meeting_history (meeting_code, action, detail) VALUES (?, ?, ?)",
        (code, "created", f"Meeting created: {title}")
    )
    conn.commit()
    conn.close()
    return code


def get_meeting(meeting_code):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        """SELECT meeting_code, title, status, meeting_link,
                  confirmed_date, confirmed_start, confirmed_end,
                  cancel_reason, created_at, archived_at
           FROM meetings WHERE meeting_code = ?""",
        (meeting_code,)
    )
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    row = list(row)
    for i in range(len(row)):
        if row[i] is None:
            row[i] = "" if i != 2 else "active"
    return tuple(row)


def update_meeting_link(meeting_code, link):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        "UPDATE meetings SET meeting_link = ? WHERE meeting_code = ?",
        (link, meeting_code)
    )
    c.execute(
        "INSERT INTO meeting_history (meeting_code, action, detail) VALUES (?, ?, ?)",
        (meeting_code, "link_updated", f"Meeting link updated: {link}")
    )
    conn.commit()
    conn.close()


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
        (meeting_code, "availability_added", f"{name} ({role}) for {date}")
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


def cancel_meeting(meeting_code, reason=""):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        "UPDATE meetings SET status = 'cancelled', cancel_reason = ?, archived_at = ? WHERE meeting_code = ?",
        (reason, now, meeting_code)
    )
    c.execute(
        "INSERT INTO meeting_history (meeting_code, action, detail) VALUES (?, ?, ?)",
        (meeting_code, "cancelled", f"Cancelled: {reason}")
    )
    conn.commit()
    conn.close()


def archive_meeting(meeting_code):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        "UPDATE meetings SET status = 'archived', archived_at = ? WHERE meeting_code = ?",
        (now, meeting_code)
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
        "UPDATE meetings SET status = 'active', cancel_reason = '', archived_at = '' WHERE meeting_code = ?",
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
        """UPDATE meetings SET status = 'confirmed',
           confirmed_date = ?, confirmed_start = ?, confirmed_end = ?
           WHERE meeting_code = ?""",
        (str(date), str(start), str(end), meeting_code)
    )
    c.execute(
        "INSERT INTO meeting_history (meeting_code, action, detail) VALUES (?, ?, ?)",
        (meeting_code, "confirmed", f"Confirmed: {date} {start}-{end}")
    )
    conn.commit()
    conn.close()


def delete_meeting_permanent(meeting_code):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM availability WHERE meeting_code = ?", (meeting_code,))
    c.execute("DELETE FROM meeting_history WHERE meeting_code = ?", (meeting_code,))
    c.execute("DELETE FROM meetings WHERE meeting_code = ?", (meeting_code,))
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
    try:
        c.execute(
            "SELECT meeting_code, title, status, created_at FROM meetings ORDER BY created_at DESC"
        )
    except sqlite3.OperationalError:
        c.execute("SELECT meeting_code, title, status, '' FROM meetings")
    rows = c.fetchall()
    conn.close()
    fixed = []
    for r in rows:
        r = list(r)
        if r[2] is None:
            r[2] = "active"
        if r[3] is None:
            r[3] = ""
        fixed.append(tuple(r))
    return fixed


def get_active_meetings():
    all_m = get_all_meetings()
    return [m for m in all_m if m[2] == "active"]


def get_archived_meetings():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    try:
        c.execute(
            """SELECT meeting_code, title, created_at, archived_at, cancel_reason
               FROM meetings WHERE status IN ('cancelled', 'archived')
               ORDER BY archived_at DESC"""
        )
    except sqlite3.OperationalError:
        c.execute(
            "SELECT meeting_code, title, '', '', '' FROM meetings WHERE status IN ('cancelled', 'archived')"
        )
    rows = c.fetchall()
    conn.close()
    fixed = []
    for r in rows:
        r = list(r)
        for i in range(len(r)):
            if r[i] is None:
                r[i] = ""
        fixed.append(tuple(r))
    return fixed


def get_confirmed_meetings():
    all_m = get_all_meetings()
    return [m for m in all_m if m[2] == "confirmed"]
