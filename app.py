import streamlit as st
import pandas as pd
from datetime import datetime
from database import (
    init_db,
    create_meeting,
    get_meeting,
    add_availability,
    get_availability
)
from ai_assistant import generate_meeting_email, parse_meeting_command


init_db()

st.set_page_config(
    page_title="MeetAlign",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)


# -----------------------------
# CSS
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

    .hero-card {
        background: #ffffff;
        padding: 30px;
        border-radius: 26px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
        margin-bottom: 26px;
    }

    .main-title {
        font-size: 42px;
        font-weight: 850;
        color: #111827;
        margin-bottom: 6px;
    }

    .subtitle {
        font-size: 17px;
        color: #6b7280;
        margin-bottom: 18px;
    }

    .section-card {
        background: #ffffff;
        padding: 24px;
        border-radius: 22px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
        margin-top: 18px;
        margin-bottom: 18px;
    }

    .guide-card {
        background: #f8fafc;
        padding: 18px 20px;
        border-radius: 18px;
        border: 1px solid #e5e7eb;
        margin-bottom: 18px;
    }

    .metric-card {
        background: #ffffff;
        padding: 18px;
        border-radius: 18px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
        text-align: center;
    }

    .metric-number {
        font-size: 30px;
        font-weight: 850;
        color: #2563eb;
    }

    .metric-label {
        font-size: 14px;
        color: #6b7280;
    }

    .empty-state {
        background: #ffffff;
        padding: 30px;
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

    [data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
    }

    .small-muted {
        font-size: 14px;
        color: #6b7280;
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

    .success-soft {
        background: #ecfdf5;
        color: #047857;
        padding: 16px;
        border-radius: 16px;
        border: 1px solid #a7f3d0;
        font-weight: 650;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------
# Texts
# -----------------------------
TEXT = {
    "English": {
        "menu": "Workspace",
        "title": "MeetAlign",
        "caption": "Smart meeting availability platform for project teams, researchers and consortium partners.",
        "hero": "Coordinate meetings without endless back-and-forth emails.",
        "hero_sub": "Create a meeting link, collect availability, find overlapping time slots, confirm a slot and generate a professional follow-up email.",

        "create": "Create Meeting",
        "add": "Add Availability",
        "view": "View Matches",
        "ai": "AI Email Assistant",
        "chat": "AI Meeting Chatbot",

        "create_header": "Create Meeting",
        "create_help": "Create a meeting title. MeetAlign will automatically generate a unique Meeting Code and shareable link.",
        "add_header": "Add Availability",
        "add_help": "Open a meeting link or enter the Meeting Code manually. Then add your name, email and availability.",
        "view_header": "View & Confirm Matching Slots",
        "view_help": "Review all submitted availability, find overlapping time slots, confirm one slot and download a calendar invite.",
        "ai_header": "AI Email Assistant",
        "ai_help": "Generate a professional email based on matching time slots.",
        "chat_header": "AI Meeting Chatbot",
        "chat_help": "Write a natural instruction such as: Plan a meeting with Moshira on 2026-05-12 at 14:00 for EIC Pathfinder.",

        "meeting_title": "Meeting Title",
        "meeting_placeholder": "EIC Pathfinder Collaboration Meeting",
        "create_button": "Create Meeting Link",
        "created_success": "Meeting link created successfully.",
        "meeting_code": "Meeting Code",
        "meeting_link": "Shareable Meeting Link",
        "copy_message": "Copy this invitation message:",
        "fill_title": "Please enter a meeting title.",

        "your_name": "Your Name",
        "your_email": "Your Email",
        "role": "Role",
        "organizer": "Organizer",
        "participant": "Participant",
        "date": "Available Date",
        "start": "Start Time",
        "end": "End Time",
        "save": "Save Availability",
        "saved": "Availability saved successfully.",
        "name_warning": "Please enter your name.",
        "code_warning": "Please enter a Meeting Code.",
        "time_warning": "End time must be later than start time.",
        "meeting_not_found": "Meeting not found. Please check the Meeting Code.",

        "all_availability": "All Availability",
        "matching_slots": "Matching Time Slots",
        "matches_found": "Matching slots found.",
        "no_matches": "No matching time slots found yet.",
        "no_data": "No availability has been added for this meeting yet.",
        "total_entries": "Availability Entries",
        "total_matches": "Matching Slots",
        "participants": "People",

        "confirm": "Confirm Meeting",
        "select_slot": "Select a slot to confirm",
        "confirmed_slot": "Confirmed Slot",
        "download_ics": "Download Calendar Invite (.ics)",

        "generate_email": "Generate Professional Email",
        "generated_email": "Generated Email",
        "email_body": "Email Body",

        "chat_input": "Write your meeting request",
        "chat_button": "Create Meeting from Chat",
        "chat_created": "Meeting created from your message.",
        "parsed_info": "AI Parsed Information",

        "col_name": "Name",
        "col_email": "Email",
        "col_role": "Role",
        "col_date": "Date",
        "col_start": "Start Time",
        "col_end": "End Time",
        "col_from": "Available From",
        "col_until": "Available Until",
    },

    "Türkçe": {
        "menu": "Çalışma Alanı",
        "title": "MeetAlign",
        "caption": "Proje ekipleri, araştırmacılar ve konsorsiyum ortakları için akıllı toplantı planlama platformu.",
        "hero": "Bitmeyen e-posta trafiği olmadan toplantı zamanı belirleyin.",
        "hero_sub": "Toplantı linki oluşturun, uygunlukları toplayın, ortak saatleri bulun, toplantıyı onaylayın ve profesyonel e-posta üretin.",

        "create": "Toplantı Oluştur",
        "add": "Uygunluk Ekle",
        "view": "Eşleşmeleri Gör",
        "ai": "AI E-posta Asistanı",
        "chat": "AI Toplantı Chatbotu",

        "create_header": "Toplantı Oluştur",
        "create_help": "Toplantı başlığını girin. MeetAlign otomatik olarak benzersiz Meeting Code ve paylaşılabilir link oluşturur.",
        "add_header": "Uygunluk Ekle",
        "add_help": "Toplantı linkini açın veya Meeting Code’u manuel girin. Ardından adınızı, e-postanızı ve uygunluk bilgilerinizi ekleyin.",
        "view_header": "Ortak Saatleri Gör ve Onayla",
        "view_help": "Girilen tüm uygunlukları görün, ortak saatleri bulun, bir saati onaylayın ve takvim davetini indirin.",
        "ai_header": "AI E-posta Asistanı",
        "ai_help": "Ortak uygun saatlere göre profesyonel e-posta oluşturun.",
        "chat_header": "AI Toplantı Chatbotu",
        "chat_help": "Doğal bir komut yazın. Örnek: 12 Mayıs 2026 saat 14:00'te Moshira ile EIC Pathfinder toplantısı planla.",

        "meeting_title": "Toplantı Başlığı",
        "meeting_placeholder": "EIC Pathfinder İş Birliği Toplantısı",
        "create_button": "Toplantı Linki Oluştur",
        "created_success": "Toplantı linki başarıyla oluşturuldu.",
        "meeting_code": "Meeting Code",
        "meeting_link": "Paylaşılabilir Toplantı Linki",
        "copy_message": "Bu davet mesajını kopyalayın:",
        "fill_title": "Lütfen toplantı başlığı girin.",

        "your_name": "Adınız",
        "your_email": "E-posta Adresiniz",
        "role": "Rol",
        "organizer": "Organizatör",
        "participant": "Katılımcı",
        "date": "Uygun Tarih",
        "start": "Başlangıç Saati",
        "end": "Bitiş Saati",
        "save": "Uygunluk Kaydet",
        "saved": "Uygunluk başarıyla kaydedildi.",
        "name_warning": "Lütfen adınızı girin.",
        "code_warning": "Lütfen Meeting Code girin.",
        "time_warning": "Bitiş saati başlangıç saatinden sonra olmalıdır.",
        "meeting_not_found": "Toplantı bulunamadı. Lütfen Meeting Code’u kontrol edin.",

        "all_availability": "Tüm Uygunluklar",
        "matching_slots": "Ortak Uygun Saatler",
        "matches_found": "Ortak uygun saat bulundu.",
        "no_matches": "Henüz ortak uygun saat bulunamadı.",
        "no_data": "Bu toplantı için henüz uygunluk eklenmemiş.",
        "total_entries": "Uygunluk Kaydı",
        "total_matches": "Ortak Saat",
        "participants": "Kişi",

        "confirm": "Toplantıyı Onayla",
        "select_slot": "Onaylanacak saati seçin",
        "confirmed_slot": "Onaylanan Saat",
        "download_ics": "Takvim Daveti İndir (.ics)",

        "generate_email": "Profesyonel E-posta Oluştur",
        "generated_email": "Oluşturulan E-posta",
        "email_body": "E-posta Metni",

        "chat_input": "Toplantı isteğinizi yazın",
        "chat_button": "Chatbot ile Toplantı Oluştur",
        "chat_created": "Mesajınızdan toplantı oluşturuldu.",
        "parsed_info": "AI Tarafından Anlaşılan Bilgi",

        "col_name": "Ad",
        "col_email": "E-posta",
        "col_role": "Rol",
        "col_date": "Tarih",
        "col_start": "Başlangıç Saati",
        "col_end": "Bitiş Saati",
        "col_from": "Uygun Başlangıç",
        "col_until": "Uygun Bitiş",
    }
}


# -----------------------------
# Helpers
# -----------------------------
def get_base_url():
    try:
        return st.context.url.split("?")[0]
    except Exception:
        return "https://your-app-url.streamlit.app"


def get_query_meeting_code():
    try:
        return st.query_params.get("meeting", "")
    except Exception:
        return ""


def set_meeting_query(meeting_code):
    st.query_params["meeting"] = meeting_code


def section_open():
    st.markdown('<div class="section-card">', unsafe_allow_html=True)


def section_close():
    st.markdown('</div>', unsafe_allow_html=True)


def guide_card(title, text):
    st.markdown(
        f"""
        <div class="guide-card">
            <strong>{title}</strong><br>
            <span class="small-muted">{text}</span>
        </div>
        """,
        unsafe_allow_html=True
    )


def metric_card(number, label):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-number">{number}</div>
            <div class="metric-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def empty_state(message):
    st.markdown(
        f"""
        <div class="empty-state">
            <h3>📭</h3>
            <p>{message}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def get_availability_dataframe(meeting_code, t):
    rows = get_availability(meeting_code)

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(
        rows,
        columns=[
            t["col_name"],
            t["col_email"],
            t["col_role"],
            t["col_date"],
            t["col_start"],
            t["col_end"]
        ]
    )


def calculate_matches(df, t):
    organizer_df = df[df[t["col_role"]] == t["organizer"]]
    participant_df = df[df[t["col_role"]] == t["participant"]]

    matches = []

    for _, organizer in organizer_df.iterrows():
        for _, participant in participant_df.iterrows():
            if organizer[t["col_date"]] == participant[t["col_date"]]:
                latest_start = max(
                    organizer[t["col_start"]],
                    participant[t["col_start"]]
                )
                earliest_end = min(
                    organizer[t["col_end"]],
                    participant[t["col_end"]]
                )

                if latest_start < earliest_end:
                    matches.append({
                        t["col_date"]: organizer[t["col_date"]],
                        t["col_from"]: latest_start,
                        t["col_until"]: earliest_end,
                        t["organizer"]: organizer[t["col_name"]],
                        t["participant"]: participant[t["col_name"]]
                    })

    return matches


def create_ics_content(title, start_date, start_time, end_time, description=""):
    start_time = str(start_time)
    end_time = str(end_time)

    if len(start_time) == 5:
        start_time += ":00"

    if len(end_time) == 5:
        end_time += ":00"

    start_dt = datetime.strptime(
        f"{start_date} {start_time}",
        "%Y-%m-%d %H:%M:%S"
    )

    end_dt = datetime.strptime(
        f"{start_date} {end_time}",
        "%Y-%m-%d %H:%M:%S"
    )

    dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dtstart = start_dt.strftime("%Y%m%dT%H%M%S")
    dtend = end_dt.strftime("%Y%m%dT%H%M%S")

    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MeetAlign//Meeting Scheduler//EN
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


# -----------------------------
# Sidebar
# -----------------------------
language = st.sidebar.selectbox(
    "Platform Language / Platform Dili",
    ["English", "Türkçe"]
)

t = TEXT[language]
query_meeting_code = get_query_meeting_code()

st.sidebar.markdown("### 📅 MeetAlign")
st.sidebar.caption("Meeting coordination workspace")

default_menu_index = 1 if query_meeting_code else 0

menu = st.sidebar.radio(
    t["menu"],
    [t["create"], t["add"], t["view"], t["ai"], t["chat"]],
    index=default_menu_index
)


# -----------------------------
# Hero
# -----------------------------
st.markdown(
    f"""
    <div class="hero-card">
        <span class="pill">Scheduling</span>
        <span class="pill">AI Assistant</span>
        <span class="pill">Calendar Invite</span>
        <div class="main-title">📅 {t["title"]}</div>
        <div class="subtitle">{t["caption"]}</div>
        <h3>{t["hero"]}</h3>
        <p class="small-muted">{t["hero_sub"]}</p>
    </div>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# Create Meeting
# -----------------------------
if menu == t["create"]:
    st.header(t["create_header"])
    guide_card("Step 1 / Adım 1", t["create_help"])

    section_open()

    meeting_title = st.text_input(
        t["meeting_title"],
        placeholder=t["meeting_placeholder"]
    )

    if st.button(t["create_button"], use_container_width=True):
        if not meeting_title:
            st.warning(t["fill_title"])
        else:
            meeting_code = create_meeting(meeting_title)
            meeting_link = f"{get_base_url()}?meeting={meeting_code}"

            st.success(t["created_success"])

            c1, c2 = st.columns([1, 2])

            with c1:
                st.text_input(t["meeting_code"], value=meeting_code)

            with c2:
                st.text_input(t["meeting_link"], value=meeting_link)

            st.write(t["copy_message"])
            st.code(
                f"""Hello,

I created a meeting availability link for:

{meeting_title}

Please add your availability using the link below:
{meeting_link}

Meeting Code: {meeting_code}

Best regards"""
            )

            set_meeting_query(meeting_code)

    section_close()


# -----------------------------
# Add Availability
# -----------------------------
elif menu == t["add"]:
    st.header(t["add_header"])
    guide_card("Step 2 / Adım 2", t["add_help"])

    section_open()

    default_code = query_meeting_code if query_meeting_code else ""

    meeting_code = st.text_input(
        t["meeting_code"],
        value=default_code,
        placeholder="AB12CD34"
    ).strip().upper()

    meeting = get_meeting(meeting_code) if meeting_code else None

    if meeting_code and meeting:
        st.success(meeting[1])

    elif meeting_code and not meeting:
        st.warning(t["meeting_not_found"])

    c1, c2 = st.columns(2)

    with c1:
        name = st.text_input(t["your_name"])
        email = st.text_input(t["your_email"])

    with c2:
        role_label = st.selectbox(t["role"], [t["organizer"], t["participant"]])
        date = st.date_input(t["date"])

        tc1, tc2 = st.columns(2)

        with tc1:
            start_time = st.time_input(t["start"])

        with tc2:
            end_time = st.time_input(t["end"])

    if st.button(t["save"], use_container_width=True):
        if not meeting_code:
            st.warning(t["code_warning"])
        elif not get_meeting(meeting_code):
            st.warning(t["meeting_not_found"])
        elif not name:
            st.warning(t["name_warning"])
        elif start_time >= end_time:
            st.warning(t["time_warning"])
        else:
            add_availability(
                meeting_code,
                name,
                email,
                role_label,
                date,
                start_time,
                end_time
            )
            st.success(t["saved"])

    section_close()


# -----------------------------
# View Matches + Confirm + ICS
# -----------------------------
elif menu == t["view"]:
    st.header(t["view_header"])
    guide_card("Step 3 / Adım 3", t["view_help"])

    default_code = query_meeting_code if query_meeting_code else ""

    meeting_code = st.text_input(
        t["meeting_code"],
        value=default_code,
        key="view_meeting_code"
    ).strip().upper()

    if not meeting_code:
        empty_state(t["code_warning"])
    else:
        meeting = get_meeting(meeting_code)

        if not meeting:
            st.warning(t["meeting_not_found"])
        else:
            st.success(meeting[1])

        df = get_availability_dataframe(meeting_code, t)

        if df.empty:
            empty_state(t["no_data"])
        else:
            matches = calculate_matches(df, t)

            m1, m2, m3 = st.columns(3)

            with m1:
                metric_card(len(df), t["total_entries"])

            with m2:
                metric_card(len(matches), t["total_matches"])

            with m3:
                metric_card(df[t["col_email"]].nunique(), t["participants"])

            section_open()
            st.subheader(t["all_availability"])
            st.dataframe(df, use_container_width=True, hide_index=True)
            section_close()

            section_open()
            st.subheader(t["matching_slots"])

            if not matches:
                st.warning(t["no_matches"])
            else:
                st.success(t["matches_found"])
                match_df = pd.DataFrame(matches)
                st.dataframe(match_df, use_container_width=True, hide_index=True)

                selected_index = st.selectbox(
                    t["select_slot"],
                    range(len(matches)),
                    format_func=lambda i: (
                        f"{matches[i][t['col_date']]} | "
                        f"{matches[i][t['col_from']]} - "
                        f"{matches[i][t['col_until']]}"
                    )
                )

                selected_match = matches[selected_index]

                if st.button(t["confirm"], use_container_width=True):
                    title = meeting[1] if meeting else "MeetAlign Meeting"

                    ics_content = create_ics_content(
                        title,
                        selected_match[t["col_date"]],
                        selected_match[t["col_from"]],
                        selected_match[t["col_until"]],
                        description=f"Meeting confirmed via MeetAlign. Meeting Code: {meeting_code}"
                    )

                    st.success(
                        f"{t['confirmed_slot']}: "
                        f"{selected_match[t['col_date']]} "
                        f"{selected_match[t['col_from']]} - "
                        f"{selected_match[t['col_until']]}"
                    )

                    st.download_button(
                        label=t["download_ics"],
                        data=ics_content,
                        file_name=f"meetalign_{meeting_code}.ics",
                        mime="text/calendar",
                        use_container_width=True
                    )

            section_close()


# -----------------------------
# AI Email Assistant
# -----------------------------
elif menu == t["ai"]:
    st.header(t["ai_header"])
    guide_card("Step 4 / Adım 4", t["ai_help"])

    section_open()

    default_code = query_meeting_code if query_meeting_code else ""

    meeting_code = st.text_input(
        t["meeting_code"],
        value=default_code,
        key="ai_meeting_code"
    ).strip().upper()

    meeting = get_meeting(meeting_code) if meeting_code else None

    meeting_title = st.text_input(
        t["meeting_title"],
        value=meeting[1] if meeting else t["meeting_placeholder"]
    )

    section_close()

    if not meeting_code:
        empty_state(t["code_warning"])
    else:
        df = get_availability_dataframe(meeting_code, t)

        if df.empty:
            empty_state(t["no_data"])
        else:
            matches = calculate_matches(df, t)

            if not matches:
                empty_state(t["no_matches"])
            else:
                section_open()
                st.subheader(t["matching_slots"])
                st.dataframe(pd.DataFrame(matches), use_container_width=True, hide_index=True)

                if st.button(t["generate_email"], use_container_width=True):
                    normalized_matches = []

                    for item in matches:
                        normalized_matches.append({
                            "Date": item[t["col_date"]],
                            "Available From": item[t["col_from"]],
                            "Available Until": item[t["col_until"]],
                        })

                    email_text = generate_meeting_email(
                        meeting_title,
                        normalized_matches
                    )

                    st.subheader(t["generated_email"])
                    st.text_area(
                        t["email_body"],
                        value=email_text,
                        height=320
                    )

                section_close()


# -----------------------------
# AI Meeting Chatbot
# -----------------------------
elif menu == t["chat"]:
    st.header(t["chat_header"])
    guide_card("AI / Yapay Zeka", t["chat_help"])

    section_open()

    user_message = st.text_area(
        t["chat_input"],
        placeholder="Plan a meeting with Moshira on 2026-05-12 at 14:00 for EIC Pathfinder.",
        height=150
    )

    if st.button(t["chat_button"], use_container_width=True):
        if not user_message:
            st.warning(t["chat_input"])
        else:
            parsed, error = parse_meeting_command(user_message)

            if error:
                st.error(error)
            else:
                meeting_title = parsed.get("meeting_title") or "MeetAlign Meeting"
                participant_name = parsed.get("participant_name", "")
                date_value = parsed.get("date", "")
                start_time = parsed.get("start_time", "")
                end_time = parsed.get("end_time", "")

                meeting_code = create_meeting(meeting_title)
                meeting_link = f"{get_base_url()}?meeting={meeting_code}"

                st.success(t["chat_created"])

                c1, c2 = st.columns([1, 2])

                with c1:
                    st.text_input(t["meeting_code"], value=meeting_code)

                with c2:
                    st.text_input(t["meeting_link"], value=meeting_link)

                st.subheader(t["parsed_info"])
                st.json(parsed)

                st.write(t["copy_message"])
                st.code(
                    f"""Hello {participant_name},

I created a meeting availability link for:

{meeting_title}

Please add your availability using the link below:
{meeting_link}

Meeting Code: {meeting_code}

Best regards"""
                )

                if date_value and start_time and end_time:
                    try:
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
                    except Exception as e:
                        st.warning(
                            f"Meeting was created, but availability could not be added: {e}"
                        )

                set_meeting_query(meeting_code)

    section_close()
