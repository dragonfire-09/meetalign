import sqlite3
from datetime import datetime
import uuid

DATABASE_FILE = "meetalign.db"


def init_db():
    """
    Veritabanını başlatır ve gerekli tabloları oluşturur.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Meetings tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_code TEXT UNIQUE,
        title TEXT
    )
    """)

    # Availability tablosu
    cursor.execute("""
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

    conn.commit()
    conn.close()


def create_meeting(title):
    """
    Yeni bir toplantı oluştur ve benzersiz bir meeting_code üretip kaydet.
    """
    meeting_code = generate_meeting_code()
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO meetings (meeting_code, title) 
    VALUES (?, ?)
    """, (meeting_code, title))

    conn.commit()
    conn.close()

    return meeting_code


def get_meeting(meeting_code):
    """
    Belirtilen meeting_code'a sahip toplantıyı veritabanından getir.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM meetings 
    WHERE meeting_code = ?
    """, (meeting_code,))

    meeting = cursor.fetchone()
    conn.close()

    return meeting


def add_availability(meeting_code, name, email, role, date, start_time, end_time):
    """
    Belirtilen meeting_code için yeni bir uygunluk kaydı ekler.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO availability (meeting_code, name, email, role, date, start_time, end_time)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (meeting_code, name, email, role, date.strftime("%Y-%m-%d"), start_time.strftime("%H:%M"), end_time.strftime("%H:%M")))

    conn.commit()
    conn.close()


def get_availability(meeting_code):
    """
    Belirtilen meeting_code'a sahip tüm uygunlukları getir.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT name, email, role, date, start_time, end_time FROM availability 
    WHERE meeting_code = ? 
    ORDER BY date, start_time
    """, (meeting_code,))

    rows = cursor.fetchall()
    conn.close()

    return rows


def generate_meeting_code():
    """
    Benzersiz bir toplantı kodu üretir. UUID'nin ilk 8 karakterini alarak oluşturur.
    """
    return str(uuid.uuid4())[:8].upper()
