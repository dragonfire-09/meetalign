import sqlite3
import string
import random
from datetime import datetime

DB = "meetalign.db"

def get_conn():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS meetings (
        code TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        video_link TEXT DEFAULT '',
        confirmed_date TEXT DEFAULT '',
        confirmed_start TEXT DEFAULT '',
        confirmed_end TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS availability (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_code TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT DEFAULT '',
        role TEXT DEFAULT 'Participant',
        date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (meeting_code) REFERENCES meetings(code)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS meeting_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_code TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (meeting_code) REFERENCES meetings(code)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_code TEXT NOT NULL,
        proposer_name TEXT NOT NULL,
        proposer_email TEXT DEFAULT '',
        proposer_role TEXT DEFAULT 'Participant',
        proposed_date TEXT NOT NULL,
        proposed_start TEXT NOT NULL,
        proposed_end TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        response_note TEXT DEFAULT '',
        responded_by TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (meeting_code) REFERENCES meetings(code)
    )""")

    conn.commit()
    conn.close()

def _gen_code(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def create_meeting(title, video_link=""):
    conn = get_conn()
    code = _gen_code()
    while conn.execute("SELECT 1 FROM meetings WHERE code=?", (code,)).fetchone():
        code = _gen_code()
    conn.execute("INSERT INTO meetings (code, title, video_link) VALUES (?,?,?)",
                 (code, title, video_link))
    conn.execute("INSERT INTO meeting_history (meeting_code, action, details) VALUES (?,?,?)",
                 (code, "created", f"Meeting '{title}' created"))
    conn.commit()
    conn.close()
    return code

def get_meeting(code):
    conn = get_conn()
    row = conn.execute(
        "SELECT code, title, status, video_link, confirmed_date, confirmed_start, confirmed_end, created_at FROM meetings WHERE code=?",
        (code,)).fetchone()
    conn.close()
    return row

def get_all_meetings():
    conn = get_conn()
    rows = conn.execute(
        "SELECT code, title, status, created_at FROM meetings ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows

def get_active_meetings():
    conn = get_conn()
    rows = conn.execute(
        "SELECT code, title, status, created_at FROM meetings WHERE status='active' ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows

def get_confirmed_meetings():
    conn = get_conn()
    rows = conn.execute(
        "SELECT code, title, status, created_at FROM meetings WHERE status='confirmed' ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows

def get_archived_meetings():
    conn = get_conn()
    rows = conn.execute(
        "SELECT code, title, status, created_at, '' FROM meetings WHERE status IN ('cancelled','archived') ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows

def update_meeting_link(code, link):
    conn = get_conn()
    conn.execute("UPDATE meetings SET video_link=?, updated_at=datetime('now') WHERE code=?", (link, code))
    conn.execute("INSERT INTO meeting_history (meeting_code, action, details) VALUES (?,?,?)",
                 (code, "link_updated", f"Video link updated"))
    conn.commit()
    conn.close()

def add_availability(meeting_code, name, email, role, date, start_time, end_time):
    conn = get_conn()
    conn.execute(
        "INSERT INTO availability (meeting_code, name, email, role, date, start_time, end_time) VALUES (?,?,?,?,?,?,?)",
        (meeting_code, name, email, role, str(date), str(start_time), str(end_time)))
    conn.execute("INSERT INTO meeting_history (meeting_code, action, details) VALUES (?,?,?)",
                 (meeting_code, "availability_added", f"{name} ({role}) — {date} {start_time}-{end_time}"))
    conn.commit()
    conn.close()

def get_availability(meeting_code):
    conn = get_conn()
    rows = conn.execute(
        "SELECT name, email, role, date, start_time, end_time FROM availability WHERE meeting_code=? ORDER BY date, start_time",
        (meeting_code,)).fetchall()
    conn.close()
    return rows

def confirm_meeting_slot(code, date, start, end):
    conn = get_conn()
    conn.execute(
        "UPDATE meetings SET status='confirmed', confirmed_date=?, confirmed_start=?, confirmed_end=?, updated_at=datetime('now') WHERE code=?",
        (str(date), str(start), str(end), code))
    conn.execute("INSERT INTO meeting_history (meeting_code, action, details) VALUES (?,?,?)",
                 (code, "confirmed", f"Confirmed: {date} {start}-{end}"))
    conn.commit()
    conn.close()

def cancel_meeting(code, reason=""):
    conn = get_conn()
    conn.execute("UPDATE meetings SET status='cancelled', updated_at=datetime('now') WHERE code=?", (code,))
    conn.execute("INSERT INTO meeting_history (meeting_code, action, details) VALUES (?,?,?)",
                 (code, "cancelled", f"Cancelled: {reason}"))
    conn.commit()
    conn.close()

def archive_meeting(code):
    conn = get_conn()
    conn.execute("UPDATE meetings SET status='archived', updated_at=datetime('now') WHERE code=?", (code,))
    conn.execute("INSERT INTO meeting_history (meeting_code, action, details) VALUES (?,?,?)",
                 (code, "archived", "Meeting archived"))
    conn.commit()
    conn.close()

def restore_meeting(code):
    conn = get_conn()
    conn.execute("UPDATE meetings SET status='active', confirmed_date='', confirmed_start='', confirmed_end='', updated_at=datetime('now') WHERE code=?", (code,))
    conn.execute("INSERT INTO meeting_history (meeting_code, action, details) VALUES (?,?,?)",
                 (code, "restored", "Meeting restored to active"))
    conn.commit()
    conn.close()

def postpone_meeting(code, reason=""):
    conn = get_conn()
    conn.execute("UPDATE meetings SET status='active', confirmed_date='', confirmed_start='', confirmed_end='', updated_at=datetime('now') WHERE code=?", (code,))
    conn.execute("INSERT INTO meeting_history (meeting_code, action, details) VALUES (?,?,?)",
                 (code, "postponed", f"Postponed: {reason}"))
    conn.commit()
    conn.close()

def delete_meeting_permanent(code):
    conn = get_conn()
    conn.execute("DELETE FROM proposals WHERE meeting_code=?", (code,))
    conn.execute("DELETE FROM availability WHERE meeting_code=?", (code,))
    conn.execute("DELETE FROM meeting_history WHERE meeting_code=?", (code,))
    conn.execute("DELETE FROM meetings WHERE code=?", (code,))
    conn.commit()
    conn.close()

def get_meeting_history(code):
    conn = get_conn()
    rows = conn.execute(
        "SELECT action, details, created_at FROM meeting_history WHERE meeting_code=? ORDER BY created_at DESC",
        (code,)).fetchall()
    conn.close()
    return rows

# ── PROPOSALS ──

def create_proposal(meeting_code, proposer_name, proposer_email, proposer_role, proposed_date, proposed_start, proposed_end):
    conn = get_conn()
    conn.execute(
        "INSERT INTO proposals (meeting_code, proposer_name, proposer_email, proposer_role, proposed_date, proposed_start, proposed_end) VALUES (?,?,?,?,?,?,?)",
        (meeting_code, proposer_name, proposer_email, proposer_role, str(proposed_date), str(proposed_start), str(proposed_end)))
    conn.execute("INSERT INTO meeting_history (meeting_code, action, details) VALUES (?,?,?)",
                 (meeting_code, "proposal_created", f"{proposer_name} proposed {proposed_date} {proposed_start}-{proposed_end}"))
    conn.commit()
    conn.close()

def get_proposals(meeting_code):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, proposer_name, proposer_email, proposer_role, proposed_date, proposed_start, proposed_end, status, response_note, responded_by, created_at FROM proposals WHERE meeting_code=? ORDER BY created_at DESC",
        (meeting_code,)).fetchall()
    conn.close()
    return rows

def get_pending_proposals(meeting_code):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, proposer_name, proposer_email, proposer_role, proposed_date, proposed_start, proposed_end, status, response_note, responded_by, created_at FROM proposals WHERE meeting_code=? AND status='pending' ORDER BY created_at DESC",
        (meeting_code,)).fetchall()
    conn.close()
    return rows

def get_all_pending_proposals():
    conn = get_conn()
    rows = conn.execute(
        "SELECT p.id, p.meeting_code, m.title, p.proposer_name, p.proposed_date, p.proposed_start, p.proposed_end, p.created_at FROM proposals p JOIN meetings m ON p.meeting_code=m.code WHERE p.status='pending' ORDER BY p.created_at DESC"
    ).fetchall()
    conn.close()
    return rows

def update_proposal(proposal_id, status, response_note="", responded_by=""):
    conn = get_conn()
    conn.execute(
        "UPDATE proposals SET status=?, response_note=?, responded_by=?, updated_at=datetime('now') WHERE id=?",
        (status, response_note, responded_by, proposal_id))
    row = conn.execute("SELECT meeting_code, proposer_name, proposed_date FROM proposals WHERE id=?", (proposal_id,)).fetchone()
    if row:
        conn.execute("INSERT INTO meeting_history (meeting_code, action, details) VALUES (?,?,?)",
                     (row[0], f"proposal_{status}", f"Proposal by {row[1]} for {row[2]}: {status}"))
    conn.commit()
    conn.close()

def get_meeting_stats():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM meetings").fetchone()[0]
    active = conn.execute("SELECT COUNT(*) FROM meetings WHERE status='active'").fetchone()[0]
    confirmed = conn.execute("SELECT COUNT(*) FROM meetings WHERE status='confirmed'").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM proposals WHERE status='pending'").fetchone()[0]
    conn.close()
    return {"total": total, "active": active, "confirmed": confirmed, "pending_proposals": pending}
