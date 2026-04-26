import streamlit as st
import pandas as pd
import sqlite3

def get_conn():
    return sqlite3.connect("meetalign.db", check_same_thread=False)

conn = get_conn()
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS availability (
    meeting_id INTEGER,
    name TEXT,
    role TEXT,
    date TEXT,
    start TEXT,
    end TEXT
)
""")

conn.commit()

st.title("📅 MeetAlign")

menu = st.sidebar.radio("Menu", ["Create Meeting", "Add Availability", "View Matches"])

if menu == "Create Meeting":
    st.header("Create Meeting")
    meeting_id = st.number_input("Choose Meeting ID", min_value=1, step=1)

    if st.button("Create"):
        st.success(f"Meeting created! Share ID: {meeting_id}")

elif menu == "Add Availability":
    st.header("Add Availability")

    meeting_id = st.number_input("Meeting ID", min_value=1)
    name = st.text_input("Your Name")
    role = st.selectbox("Role", ["Organizer", "Participant"])

    date = st.date_input("Date")
    start = st.time_input("Start Time")
    end = st.time_input("End Time")

    if st.button("Save"):
        cur.execute("""
        INSERT INTO availability VALUES (?, ?, ?, ?, ?, ?)
        """, (meeting_id, name, role, str(date), str(start), str(end)))
        conn.commit()
        st.success("Saved!")

elif menu == "View Matches":
    st.header("Matches")

    meeting_id = st.number_input("Meeting ID", min_value=1, key="view")

    df = pd.read_sql_query(f"""
    SELECT * FROM availability WHERE meeting_id = {meeting_id}
    """, conn)

    if not df.empty:
        st.dataframe(df)

        org = df[df["role"] == "Organizer"]
        part = df[df["role"] == "Participant"]

        matches = []

        for _, o in org.iterrows():
            for _, p in part.iterrows():
                if o["date"] == p["date"]:
                    if o["start"] < p["end"] and p["start"] < o["end"]:
                        matches.append({
                            "date": o["date"],
                            "start": max(o["start"], p["start"]),
                            "end": min(o["end"], p["end"])
                        })

        if matches:
            st.success("Matching slots found!")
            st.dataframe(pd.DataFrame(matches))
        else:
            st.warning("No matches yet.")
    else:
        st.info("No data yet.")
