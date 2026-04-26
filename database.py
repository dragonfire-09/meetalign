import sqlite3

DB_NAME = "meetalign.db"

def init_db():
    """Veritabanını başlatır ve gerekli tabloları oluşturur."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Meetings tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS meetings (
                    code TEXT PRIMARY KEY,
                    title TEXT
                )''')

    # Availability tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS availability (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meeting_code TEXT,
                    name TEXT,
                    email TEXT,
                    role TEXT,
                    date TEXT,
                    start_time TEXT,
                    end_time TEXT
                )''')

    conn.commit()
    conn.close()


def create_meeting(title):
    """Yeni bir toplantı oluşturur ve eşsiz bir kod döner."""
    import uuid
    meeting_code = uuid.uuid4().hex[:8].upper()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO meetings (code, title) VALUES (?, ?)", (meeting_code, title))
    conn.commit()
    conn.close()
    return meeting_code


def get_meeting(meeting_code):
    """Verilen kod ile toplantıyı getirir."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT code, title FROM meetings WHERE code = ?", (meeting_code,))
    meeting = c.fetchone()
    conn.close()
    return meeting


def add_availability(meeting_code, name, email, role, date, start_time, end_time):
    """Belirli bir toplantıya uygunluk kaydı ekler."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''INSERT INTO availability 
                 (meeting_code, name, email, role, date, start_time, end_time)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (meeting_code, name, email, role, date, start_time, end_time))
    conn.commit()
    conn.close()


def get_availability(meeting_code):
    """Belirli bir toplantının tüm uygunluk kayıtlarını getirir."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''SELECT name, email, role, date, start_time, end_time 
                 FROM availability WHERE meeting_code = ?''', (meeting_code,))
    rows = c.fetchall()
    conn.close()
    return rows
