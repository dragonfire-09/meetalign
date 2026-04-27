import sqlite3
import random
import string
from datetime import datetime

DB = "meetalign.db"

def _conn():
    return sqlite3.connect(DB)

def init_db():
    c = _conn()
    cur = c.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            code TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT,
            confirmed_date TEXT,
            confirmed_start TEXT,
            confirmed_end TEXT,
            video_link TEXT DEFAULT '',
            cancel_reason TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_code TEXT,
            name TEXT,
            email TEXT,
            role TEXT,
            date TEXT,
            start_time TEXT,
            end_time TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_code TEXT,
            proposer_name TEXT,
            proposer_email TEXT,
            proposer_role TEXT,
            proposed_date TEXT,
            proposed_start TEXT,
            proposed_end TEXT,
            status TEXT DEFAULT 'pending',
            note TEXT DEFAULT '',
            response_note TEXT DEFAULT '',
            created_at TEXT,
            responded_at TEXT DEFAULT '',
            responded_by TEXT DEFAULT ''
        )
    """)

    # counter_proposal kolonu — yoksa ekle
    try:
        cur.execute("ALTER TABLE proposals ADD COLUMN counter_proposal_id INTEGER DEFAULT NULL")
    except Exception:
        pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS meeting_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_code TEXT,
            action TEXT,
            detail TEXT,
            timestamp TEXT
        )
    """)

    c.commit()
    c.close()


def _gen_code():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def _log(code, action, detail=""):
    c = _conn()
    c.execute(
        "INSERT INTO meeting_history (meeting_code, action, detail, timestamp) VALUES (?,?,?,?)",
        (code, action, detail, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    c.commit()
    c.close()


# ═══════════════════════════════════════
# MEETINGS
# ═══════════════════════════════════════

def create_meeting(title, video_link=""):
    code = _gen_code()
    c = _conn()
    c.execute(
        "INSERT INTO meetings (code, title, status, created_at, video_link) VALUES (?,?,?,?,?)",
        (code, title, "active", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), video_link or "")
    )
    c.commit()
    c.close()
    _log(code, "created", title)
    return code


def get_meeting(code):
    c = _conn()
    row = c.execute(
        "SELECT code, title, status, created_at, confirmed_date, confirmed_start, confirmed_end, video_link, cancel_reason "
        "FROM meetings WHERE code=?", (code.upper(),)
    ).fetchone()
    c.close()
    return row


def update_meeting_link(code, link):
    c = _conn()
    c.execute("UPDATE meetings SET video_link=? WHERE code=?", (link, code))
    c.commit()
    c.close()
    _log(code, "video_link_updated", link)


def get_all_meetings():
    c = _conn()
    rows = c.execute(
        "SELECT code, title, status, created_at FROM meetings ORDER BY created_at DESC"
    ).fetchall()
    c.close()
    return rows


def get_active_meetings():
    c = _conn()
    rows = c.execute(
        "SELECT code, title, status, created_at FROM meetings WHERE status='active' ORDER BY created_at DESC"
    ).fetchall()
    c.close()
    return rows


def get_confirmed_meetings():
    c = _conn()
    rows = c.execute(
        "SELECT code, title, status, created_at FROM meetings WHERE status='confirmed' ORDER BY created_at DESC"
    ).fetchall()
    c.close()
    return rows


def get_archived_meetings():
    c = _conn()
    rows = c.execute(
        "SELECT code, title, status, created_at, cancel_reason FROM meetings "
        "WHERE status IN ('cancelled','archived') ORDER BY created_at DESC"
    ).fetchall()
    c.close()
    return rows


def confirm_meeting_slot(code, date, start, end):
    c = _conn()
    c.execute(
        "UPDATE meetings SET status='confirmed', confirmed_date=?, confirmed_start=?, confirmed_end=? WHERE code=?",
        (str(date), str(start), str(end), code)
    )
    c.commit()
    c.close()
    _log(code, "confirmed", "{} {}-{}".format(date, start, end))


def cancel_meeting(code, reason=""):
    c = _conn()
    c.execute("UPDATE meetings SET status='cancelled', cancel_reason=? WHERE code=?", (reason, code))
    c.commit()
    c.close()
    _log(code, "cancelled", reason)


def archive_meeting(code):
    c = _conn()
    c.execute("UPDATE meetings SET status='archived' WHERE code=?", (code,))
    c.commit()
    c.close()
    _log(code, "archived")


def restore_meeting(code):
    c = _conn()
    c.execute("UPDATE meetings SET status='active' WHERE code=?", (code,))
    c.commit()
    c.close()
    _log(code, "restored")


def delete_meeting_permanent(code):
    c = _conn()
    c.execute("DELETE FROM meetings WHERE code=?", (code,))
    c.execute("DELETE FROM availability WHERE meeting_code=?", (code,))
    c.execute("DELETE FROM proposals WHERE meeting_code=?", (code,))
    c.execute("DELETE FROM meeting_history WHERE meeting_code=?", (code,))
    c.commit()
    c.close()


def postpone_meeting(code, reason=""):
    """Active veya confirmed her ikisi için çalışır. Uygunlukları temizler."""
    c = _conn()
    # Her iki durumda da çalış
    c.execute(
        "UPDATE meetings SET status='active', confirmed_date=NULL, confirmed_start=NULL, confirmed_end=NULL WHERE code=?",
        (code,)
    )
    # Eski uygunlukları sil (isteğe bağlı — eski kayıtlar kalmasın)
    c.execute("DELETE FROM availability WHERE meeting_code=?", (code,))
    # Pending teklifleri expire et
    c.execute(
        "UPDATE proposals SET status='expired' WHERE meeting_code=? AND status='pending'",
        (code,)
    )
    c.commit()
    c.close()
    _log(code, "postponed", reason)


def get_meeting_stats():
    c = _conn()
    total = c.execute("SELECT COUNT(*) FROM meetings").fetchone()[0]
    active = c.execute("SELECT COUNT(*) FROM meetings WHERE status='active'").fetchone()[0]
    confirmed = c.execute("SELECT COUNT(*) FROM meetings WHERE status='confirmed'").fetchone()[0]
    pending_proposals = c.execute("SELECT COUNT(*) FROM proposals WHERE status='pending'").fetchone()[0]
    c.close()
    return {
        "total": total,
        "active": active,
        "confirmed": confirmed,
        "pending_proposals": pending_proposals
    }


# ═══════════════════════════════════════
# AVAILABILITY
# ═══════════════════════════════════════

def add_availability(code, name, email, role, date, start, end):
    c = _conn()
    c.execute(
        "INSERT INTO availability (meeting_code, name, email, role, date, start_time, end_time) VALUES (?,?,?,?,?,?,?)",
        (code, name, email or "", role, str(date), str(start), str(end))
    )
    c.commit()
    c.close()


def get_availability(code):
    c = _conn()
    rows = c.execute(
        "SELECT name, email, role, date, start_time, end_time FROM availability WHERE meeting_code=? ORDER BY date, start_time",
        (code,)
    ).fetchall()
    c.close()
    return rows


def clear_availability(code):
    """Belirli bir toplantının tüm uygunluklarını sil."""
    c = _conn()
    c.execute("DELETE FROM availability WHERE meeting_code=?", (code,))
    c.commit()
    c.close()
    _log(code, "availability_cleared")


# ═══════════════════════════════════════
# PROPOSALS
# ═══════════════════════════════════════

def create_proposal(code, name, email, role, date, start, end, note="", counter_of=None):
    """Yeni teklif oluştur."""
    c = _conn()
    c.execute(
        "INSERT INTO proposals "
        "(meeting_code, proposer_name, proposer_email, proposer_role, proposed_date, proposed_start, proposed_end, "
        "status, note, created_at, counter_proposal_id) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            code, name, email or "", role,
            str(date), str(start), str(end),
            "pending", note or "",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            counter_of
        )
    )
    c.commit()
    c.close()
    _log(code, "proposal_created", "{} proposed {}: {}-{}".format(name, date, start, end))


def get_proposals(code):
    """Bir toplantının tüm tekliflerini getir."""
    c = _conn()
    rows = c.execute(
        "SELECT id, proposer_name, proposer_email, proposer_role, proposed_date, proposed_start, proposed_end, "
        "status, note, response_note, created_at "
        "FROM proposals WHERE meeting_code=? ORDER BY created_at DESC",
        (code,)
    ).fetchall()
    c.close()
    return rows


def get_pending_proposals(code):
    """Bekleyen teklifleri getir."""
    c = _conn()
    rows = c.execute(
        "SELECT id, proposer_name, proposer_email, proposer_role, proposed_date, proposed_start, proposed_end, "
        "status, note, response_note, created_at "
        "FROM proposals WHERE meeting_code=? AND status='pending' ORDER BY created_at DESC",
        (code,)
    ).fetchall()
    c.close()
    return rows


def get_all_pending_proposals():
    """Tüm toplantılardaki bekleyen teklifleri getir (dashboard için)."""
    c = _conn()
    rows = c.execute(
        "SELECT p.id, p.meeting_code, m.title, p.proposer_name, p.proposed_date, "
        "p.proposed_start, p.proposed_end, p.created_at "
        "FROM proposals p JOIN meetings m ON p.meeting_code = m.code "
        "WHERE p.status='pending' ORDER BY p.created_at DESC"
    ).fetchall()
    c.close()
    return rows


def update_proposal(pid, status, response_note="", responded_by=""):
    """Teklifi güncelle. Kabul edilirse diğer pending'leri expire et."""
    c = _conn()

    # Önce bu proposal'ın hangi meeting'e ait olduğunu bul
    row = c.execute("SELECT meeting_code FROM proposals WHERE id=?", (pid,)).fetchone()
    meeting_code = row[0] if row else None

    # Teklifi güncelle
    c.execute(
        "UPDATE proposals SET status=?, response_note=?, responded_by=?, responded_at=? WHERE id=?",
        (
            status,
            response_note or "",
            responded_by or "",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            pid
        )
    )

    # Kabul edilirse — diğer pending teklifleri expire et
    if status == "accepted" and meeting_code:
        c.execute(
            "UPDATE proposals SET status='expired', responded_at=? "
            "WHERE meeting_code=? AND id!=? AND status='pending'",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), meeting_code, pid)
        )

    c.commit()
    c.close()

    if meeting_code:
        _log(meeting_code, "proposal_{}".format(status), "pid={}".format(pid))


def expire_other_proposals(code, accepted_pid):
    """Kabul edilen dışındaki tüm pending teklifleri expire et."""
    c = _conn()
    c.execute(
        "UPDATE proposals SET status='expired', responded_at=? "
        "WHERE meeting_code=? AND id!=? AND status='pending'",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), code, accepted_pid)
    )
    c.commit()
    c.close()


# ═══════════════════════════════════════
# HISTORY
# ═══════════════════════════════════════

def get_meeting_history(code):
    c = _conn()
    rows = c.execute(
        "SELECT action, detail, timestamp FROM meeting_history WHERE meeting_code=? ORDER BY timestamp DESC",
        (code,)
    ).fetchall()
    c.close()
    return rows
