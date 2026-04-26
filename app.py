import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from database import (
    init_db,
    create_meeting,
    get_meeting,
    add_availability,
    get_availability
)
from ai_assistant import parse_meeting_command


init_db()

st.set_page_config(
    page_title="MeetAlign",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)


# -----------------------------
# STYLE
# -----------------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
    }

    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e5e7eb;
    }

    .hero {
        background: #ffffff;
        padding: 30px;
        border-radius: 26px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
        margin-bottom: 24px;
    }

    .hero-title {
        font-size: 42px;
        font-weight: 850;
        color: #111827;
        margin-bottom: 8px;
    }

    .hero-sub {
        color: #6b7280;
        font-size: 17px;
    }

    .card {
        background: #ffffff;
        padding: 24px;
        border-radius: 22px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
        margin-top: 18px;
        margin-bottom: 18px;
    }

    .guide {
        background: #f8fafc;
        padding: 16px 18px;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        color: #475569;
        margin-bottom: 18px;
    }

    .pill {
        display: inline-block;
        padding: 7px 12px;
        background: #eff6ff;
        color: #1d4ed8;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 700;
        margin-right: 8px;
        border: 1px solid #bfdbfe;
    }

    .empty {
        background: #ffffff;
        padding: 28px;
        border-radius: 22px;
        border: 1px dashed #cbd5e1;
        text-align: center;
        color: #64748b;
        margin-top: 18px;
    }

    div.stButton > button {
        background: linear-gradient(90deg, #2563eb, #4f46e5);
        color: white;
        border: none;
        border-radius: 14px;
        padding: 0.75rem 1.25rem;
        font-weight: 750;
        box-shadow: 0 10px 24px rgba(37, 99, 235, 0.28);
    }

    div.stButton > button:hover {
        background: linear-gradient(90deg, #1d4ed8, #4338ca);
        color: white;
        border: none;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------
# TEXT
# -----------------------------
TEXT = {
    "English": {
        "menu": "Workspace",
        "create": "Create Meeting",
        "availability": "Add Availability",
        "confirm": "Confirm & Calendar",
        "chatbot": "AI Chatbot",

        "title": "MeetAlign",
        "subtitle": "Smart meeting scheduler for project teams, researchers and consortium partners.",
        "hero": "Create a link, collect availability, confirm a slot and send a calendar invite.",

        "meeting_title": "Meeting Title",
        "meeting_placeholder": "EIC Pathfinder Collaboration Meeting",
        "create_button": "Create Meeting Link",
        "meeting_code": "Meeting Code",
        "meeting_link": "Meeting Link",
        "copy_invitation": "Copy invitation message",
        "created": "Meeting created successfully.",

        "name": "Your Name",
        "email": "Your Email",
        "role": "Role",
        "organizer": "Organizer",
        "participant": "Participant",
        "date": "Date",
        "start": "Start Time",
        "end": "End Time",
        "save": "Save Availability",
        "saved": "Availability saved.",
        "not_found": "Meeting not found.",
        "enter_code": "Please enter Meeting Code.",
        "enter_name": "Please enter your name.",
        "time_error": "End time must be later than start time.",

        "all_availability": "All Availability",
        "matches": "Matching Slots",
        "no_data": "No availability has been added yet.",
        "no_match": "No matching slot found yet.",
        "select_slot": "Select slot to confirm",
        "confirm_meeting": "Confirm Meeting",
        "confirmed": "Meeting confirmed.",
        "download_ics": "Download .ics Calendar Invite",

        "google_meet": "Google Meet",
        "google_coming": "Coming Soon — Connect Google Calendar to generate Google Meet links automatically.",

        "send_email": "Send Confirmation Email",
        "recipient_email": "Recipient Email",
        "email_sent": "Confirmation email sent.",
        "email_failed": "Email could not be sent.",

        "chat_help": "Example: Plan a meeting with Moshira on 2026-05-12 at 14:00 for EIC Pathfinder.",
        "chat_input": "Write your meeting request",
        "chat_button": "Create Meeting from Chat",
        "parsed": "AI understood this:",
    },
    "Türkçe": {
        "menu": "Çalışma Alanı",
        "create": "Toplantı Oluştur",
        "availability": "Uygunluk Ekle",
        "confirm": "Onayla & Takvim",
        "chatbot": "AI Chatbot",

        "title": "MeetAlign",
        "subtitle": "Proje ekipleri, araştırmacılar ve konsorsiyum ortakları için akıllı toplantı planlayıcı.",
        "hero": "Link oluşturun, uygunlukları toplayın, ortak saati onaylayın ve takvim daveti gönderin.",

        "meeting_title": "Toplantı Başlığı",
        "meeting_placeholder": "EIC Pathfinder İş Birliği Toplantısı",
        "create_button": "Toplantı Linki Oluştur",
        "meeting_code": "Meeting Code",
        "meeting_link": "Toplantı Linki",
        "copy_invitation": "Davet mesajını kopyala",
        "created": "Toplantı başarıyla oluşturuldu.",

        "name": "Adınız",
        "email": "E-posta Adresiniz",
        "role": "Rol",
        "organizer": "Organizatör",
        "participant": "Katılımcı",
        "date": "Tarih",
        "start": "Başlangıç Saati",
        "end": "Bitiş Saati",
        "save": "Uygunluk Kaydet",
        "saved": "Uygunluk kaydedildi.",
        "not_found": "Toplantı bulunamadı.",
        "enter_code": "Lütfen Meeting Code girin.",
        "enter_name": "Lütfen adınızı girin.",
        "time_error": "Bitiş saati başlangıç saatinden sonra olmalıdır.",

        "all_availability": "Tüm Uygunluklar",
        "matches": "Ortak Uygun Saatler",
        "no_data": "Henüz uygunluk eklenmemiş.",
        "no_match": "Henüz ortak saat bulunamadı.",
        "select_slot": "Onaylanacak saati seçin",
        "confirm_meeting": "Toplantıyı Onayla",
        "confirmed": "Toplantı onaylandı.",
        "download_ics": ".ics Takvim Daveti İndir",

        "google_meet": "Google Meet",
        "google_coming": "Yakında — Google Calendar bağlandığında Google Meet linki otomatik üretilecek.",

        "send_email": "Onay E-postası Gönder",
        "recipient_email": "Alıcı E-posta",
        "email_sent": "Onay e-postası gönderildi.",
        "email_failed": "E-posta gönderilemedi.",

        "chat_help": "Örnek: 12 Mayıs 2026 saat 14:00'te Moshira ile EIC Pathfinder toplantısı planla.",
        "chat_input": "Toplantı isteğinizi yazın",
        "chat_button": "Chatbot ile Toplantı Oluştur",
        "parsed": "AI bunu anladı:",
    }
}


# -----------------------------
# HELPERS
# -----------------------------
def get_base_url():
    try:
        return st.context.url.split("?")[0]
    except Exception:
        return "https://your-app-url.streamlit.app"


def get_query_code():
    try:
        return st.query_params.get("meeting", "")
    except Exception:
        return ""


def card_start():
    st.markdown('<div class="card">', unsafe_allow_html=True)


def card_end():
    st.markdown('</div>', unsafe_allow_html=True)


def guide(text):
    st.markdown(f'<div class="guide">{text}</div>', unsafe_allow_html=True)


def empty(message):
    st.markdown(
        f"""
        <div class="empty">
            <h3>📭</h3>
            <p>{message}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def get_df(meeting_code):
    rows = get_availability(meeting_code)

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(
        rows,
        columns=["Name", "Email", "Role", "Date", "Start Time", "End Time"]
    )


def calculate_matches(df, organizer_label, participant_label):
    organizers = df[df["Role"] == organizer_label]
    participants = df[df["Role"] == participant_label]

    matches = []

    for _, org in organizers.iterrows():
        for _, part in participants.iterrows():
            if org["Date"] == part["Date"]:
                start = max(org["Start Time"], part["Start Time"])
                end = min(org["End Time"], part["End Time"])

                if start < end:
                    matches.append({
                        "Date": org["Date"],
                        "Start": start,
                        "End": end,
                        "Organizer": org["Name"],
                        "Participant": part["Name"],
                        "Participant Email": part["Email"]
                    })

    return matches


def create_ics(title, date, start_time, end_time, description=""):
    start_time = str(start_time)
    end_time = str(end_time)

    if len(start_time) == 5:
        start_time += ":00"

    if len(end_time) == 5:
        end_time += ":00"

    start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M:%S")

    dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dtstart = start_dt.strftime("%Y%m%dT%H%M%S")
    dtend = end_dt.strftime("%Y%m%dT%H%M%S")

    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MeetAlign//EN
BEGIN:VEVENT
UID:{dtstamp}@meetalign
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:{title}
DESCRIPTION:{description}
END:VEVENT
END:VCALENDAR
"""


def send_resend_email(to_email, subject, body):
    api_key = st.secrets.get("RESEND_API_KEY", None)
    sender_email = st.secrets.get("SENDER_EMAIL", None)

    if not api_key or not sender_email:
        return False, "RESEND_API_KEY or SENDER_EMAIL is missing in Streamlit Secrets."

    payload = {
        "from": sender_email,
        "to": [to_email],
        "subject": subject,
        "html": body.replace("\n", "<br>")
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code in [200, 201, 202]:
            return True, response.text

        return False, response.text

    except Exception as e:
        return False, str(e)


# -----------------------------
# SIDEBAR
# -----------------------------
language = st.sidebar.selectbox(
    "Platform Language / Platform Dili",
    ["English", "Türkçe"]
)

t = TEXT[language]
query_code = get_query_code()

st.sidebar.markdown("### 📅 MeetAlign")

menu = st.sidebar.radio(
    t["menu"],
    [t["create"], t["availability"], t["confirm"], t["chatbot"]],
    index=1 if query_code else 0
)


# -----------------------------
# HERO
# -----------------------------
st.markdown(
    f"""
    <div class="hero">
        <span class="pill">Availability</span>
        <span class="pill">Calendar Invite</span>
        <span class="pill">AI Chatbot</span>
        <div class="hero-title">📅 {t["title"]}</div>
        <div class="hero-sub">{t["subtitle"]}</div>
        <h3>{t["hero"]}</h3>
    </div>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# CREATE MEETING
# -----------------------------
if menu == t["create"]:
    st.header(t["create"])

    guide("1. Enter a meeting title. 2. Create a link. 3. Share it with the other person.")

    card_start()

    meeting_title = st.text_input(
        t["meeting_title"],
        placeholder=t["meeting_placeholder"]
    )

    if st.button(t["create_button"], use_container_width=True):
        if not meeting_title:
            st.warning(t["meeting_title"])
        else:
            meeting_code = create_meeting(meeting_title)
            meeting_link = f"{get_base_url()}?meeting={meeting_code}"

            st.success(t["created"])

            c1, c2 = st.columns([1, 2])

            with c1:
                st.text_input(t["meeting_code"], value=meeting_code)

            with c2:
                st.text_input(t["meeting_link"], value=meeting_link)

            st.subheader(t["copy_invitation"])
            st.code(
                f"""Hello,

I created a meeting availability link for:

{meeting_title}

Please add your availability using the link below:
{meeting_link}

Meeting Code: {meeting_code}

Best regards"""
            )

    card_end()


# -----------------------------
# ADD AVAILABILITY
# -----------------------------
elif menu == t["availability"]:
    st.header(t["availability"])

    guide("1. Open the meeting link or enter Meeting Code. 2. Add your availability. 3. Save.")

    card_start()

    meeting_code = st.text_input(
        t["meeting_code"],
        value=query_code,
        placeholder="AB12CD34"
    ).strip().upper()

    meeting = get_meeting(meeting_code) if meeting_code else None

    if meeting:
        st.success(meeting[1])
    elif meeting_code:
        st.warning(t["not_found"])

    c1, c2 = st.columns(2)

    with c1:
        name = st.text_input(t["name"])
        email = st.text_input(t["email"])

    with c2:
        role = st.selectbox(t["role"], [t["organizer"], t["participant"]])
        date = st.date_input(t["date"])

        sc1, sc2 = st.columns(2)
        with sc1:
            start_time = st.time_input(t["start"])
        with sc2:
            end_time = st.time_input(t["end"])

    if st.button(t["save"], use_container_width=True):
        if not meeting_code:
            st.warning(t["enter_code"])
        elif not get_meeting(meeting_code):
            st.warning(t["not_found"])
        elif not name:
            st.warning(t["enter_name"])
        elif start_time >= end_time:
            st.warning(t["time_error"])
        else:
            add_availability(
                meeting_code,
                name,
                email,
                role,
                date,
                start_time,
                end_time
            )
            st.success(t["saved"])

    card_end()


# -----------------------------
# CONFIRM + ICS + EMAIL
# -----------------------------
elif menu == t["confirm"]:
    st.header(t["confirm"])

    guide("1. Enter Meeting Code. 2. Select a matching slot. 3. Download .ics or send confirmation email.")

    card_start()

    meeting_code = st.text_input(
        t["meeting_code"],
        value=query_code,
        key="confirm_code"
    ).strip().upper()

    meeting = get_meeting(meeting_code) if meeting_code else None

    if not meeting_code:
        st.info(t["enter_code"])
        card_end()
        st.stop()

    if not meeting:
        st.warning(t["not_found"])
        card_end()
        st.stop()

    meeting_title = meeting[1]
    st.success(meeting_title)

    df = get_df(meeting_code)

    if df.empty:
        empty(t["no_data"])
        card_end()
        st.stop()

    st.subheader(t["all_availability"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    matches = calculate_matches(df, t["organizer"], t["participant"])

    st.subheader(t["matches"])

    if not matches:
        empty(t["no_match"])
        card_end()
        st.stop()

    match_df = pd.DataFrame(matches)
    st.dataframe(match_df, use_container_width=True, hide_index=True)

    selected_index = st.selectbox(
        t["select_slot"],
        range(len(matches)),
        format_func=lambda i: f"{matches[i]['Date']} | {matches[i]['Start']} - {matches[i]['End']}"
    )

    selected = matches[selected_index]

    st.markdown("### ✅ Selected Slot")
    st.info(f"{selected['Date']} | {selected['Start']} - {selected['End']}")

    st.markdown("### 🔗 Google Meet")
    st.warning(t["google_coming"])

    if st.button(t["confirm_meeting"], use_container_width=True):
        ics_content = create_ics(
            meeting_title,
            selected["Date"],
            selected["Start"],
            selected["End"],
            description=f"Meeting confirmed via MeetAlign. Meeting Code: {meeting_code}"
        )

        st.success(t["confirmed"])

        st.download_button(
            label=t["download_ics"],
            data=ics_content,
            file_name=f"meetalign_{meeting_code}.ics",
            mime="text/calendar",
            use_container_width=True
        )

    st.markdown("### ✉️ Email Confirmation")

    recipient_email = st.text_input(
        t["recipient_email"],
        value=selected.get("Participant Email", "")
    )

    email_body = f"""Hello,

The meeting has been confirmed.

Meeting: {meeting_title}
Date: {selected['Date']}
Time: {selected['Start']} - {selected['End']}

Google Meet:
Coming Soon — Google Calendar connection will be available in a future version.

Best regards,
MeetAlign
"""

    st.text_area("Email Preview", value=email_body, height=180)

    if st.button(t["send_email"], use_container_width=True):
        if not recipient_email:
            st.warning(t["recipient_email"])
        else:
            ok, message = send_resend_email(
                recipient_email,
                f"Confirmed Meeting: {meeting_title}",
                email_body
            )

            if ok:
                st.success(t["email_sent"])
            else:
                st.error(f"{t['email_failed']} {message}")

    card_end()


# -----------------------------
# AI CHATBOT
# -----------------------------
elif menu == t["chatbot"]:
    st.header(t["chatbot"])

    guide(t["chat_help"])

    card_start()

    user_message = st.text_area(
        t["chat_input"],
        height=150,
        placeholder=t["chat_help"]
    )

    if st.button(t["chat_button"], use_container_width=True):
        if not user_message:
            st.warning(t["chat_input"])
        else:
            parsed, error = parse_meeting_command(user_message)

            if error:
                st.error(error)
            else:
                st.subheader(t["parsed"])
                st.json(parsed)

                meeting_title = parsed.get("meeting_title") or "MeetAlign Meeting"
                date_value = parsed.get("date", "")
                start_time = parsed.get("start_time", "")
                end_time = parsed.get("end_time", "")
                participant_name = parsed.get("participant_name", "")

                if start_time and not end_time:
                    try:
                        temp = datetime.strptime(start_time, "%H:%M")
                        end_time = (temp + timedelta(minutes=30)).strftime("%H:%M")
                    except Exception:
                        end_time = ""

                meeting_code = create_meeting(meeting_title)
                meeting_link = f"{get_base_url()}?meeting={meeting_code}"

                st.success(t["created"])

                c1, c2 = st.columns([1, 2])

                with c1:
                    st.text_input(t["meeting_code"], value=meeting_code)

                with c2:
                    st.text_input(t["meeting_link"], value=meeting_link)

                if date_value and start_time and end_time:
                    add_availability(
                        meeting_code,
                        "Organizer",
                        "",
                        t["organizer"],
                        date_value,
                        f"{start_time}:00" if len(start_time) == 5 else start_time,
                        f"{end_time}:00" if len(end_time) == 5 else end_time
                    )

                    st.info("Organizer availability was added automatically.")

                st.subheader(t["copy_invitation"])
                st.code(
                    f"""Hello {participant_name},

I created a meeting availability link for:

{meeting_title}

Please add your availability using the link below:
{meeting_link}

Meeting Code: {meeting_code}

Best regards"""
                )

    card_end()
