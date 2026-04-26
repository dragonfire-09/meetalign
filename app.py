import streamlit as st
import pandas as pd
from database import (
    init_db,
    create_meeting,
    get_meeting,
    add_availability,
    get_availability
)
from ai_assistant import generate_meeting_email, ai_chatbot_response, test_openrouter_connection

# Veritabanını başlat (ilk çalışmada gerekli)
init_db()

# Streamlit uygulama genel yapılandırması
st.set_page_config(
    page_title="MeetAlign",
    page_icon="📅",
    layout="wide"
)

# Stil ve CSS
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
        padding: 28px;
        border-radius: 24px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
        margin-bottom: 24px;
    }

    .main-title {
        font-size: 42px;
        font-weight: 800;
        color: #111827;
        margin-bottom: 4px;
    }

    .subtitle {
        font-size: 17px;
        color: #6b7280;
        margin-bottom: 16px;
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

    .step-card {
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
        font-size: 28px;
        font-weight: 800;
        color: #2563eb;
    }

    .metric-label {
        font-size: 14px;
        color: #6b7280;
    }

    .empty-state {
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
        padding: 0.7rem 1.2rem;
        font-weight: 700;
        box-shadow: 0 10px 24px rgba(37, 99, 235, 0.28);
    }

    div.stButton > button:hover {
        background: linear-gradient(90deg, #1d4ed8, #4338ca);
        color: white;
        border: none;
    }

    .small-muted {
        font-size: 14px;
        color: #6b7280;
    }
</style>
""", unsafe_allow_html=True)

# Çoklu dil desteği metinleri
TEXT = {
    "English": {
        "title": "MeetAlign",
        "caption": "Smart meeting availability platform for project teams, researchers and consortium partners.",
        "menu": "Workspace",
        "create": "Create Meeting",
        "add": "Add Availability",
        "view": "View Matches",
        "ai": "AI Email Assistant",
        "hero": "Coordinate meetings without endless back-and-forth emails.",
        "hero_sub": "Create a meeting link, collect availability, find overlapping time slots and generate a professional follow-up email.",
        "create_header": "Create Meeting",
        "create_help": "Create a new meeting. The platform will generate a unique Meeting Code and shareable link.",
        "add_header": "Add Availability",
        "add_help": "Open the meeting link or enter the Meeting Code manually, then add your availability.",
        "view_header": "View Matching Slots",
        "view_help": "Review all availability and identify overlapping time windows.",
        "ai_header": "AI Email Assistant",
        "ai_help": "Generate a professional meeting email from the matched time slots.",
        "meeting_code": "Meeting Code",
        "meeting_link": "Shareable Meeting Link",
        "meeting_title": "Meeting Title",
        "meeting_placeholder": "EIC Pathfinder Collaboration Meeting",
        "create_button": "Create Meeting Link",
        "created_success": "Meeting link created successfully.",
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
        "name_warning": "Please enter your name.",
        "code_warning": "Please enter a Meeting Code.",
        "time_warning": "End time must be later than start time.",
        "saved": "Availability saved successfully.",
        "all_availability": "All Availability",
        "matching_slots": "Matching Time Slots",
        "matches_found": "Matching slots found.",
        "no_matches": "No matching time slots found yet.",
        "no_data": "No availability has been added for this meeting yet.",
        "meeting_not_found": "Meeting not found. Please check the Meeting Code.",
        "generate_email": "Generate Professional Email",
        "generated_email": "Generated Email",
        "email_body": "Email Body",
        "total_entries": "Availability Entries",
        "total_matches": "Matching Slots",
        "participants": "People",
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
        "title": "MeetAlign",
        "caption": "Proje ekipleri, araştırmacılar ve konsorsiyum ortakları için akıllı toplantı planlama platformu.",
        "menu": "Çalışma Alanı",
        "create": "Toplantı Oluştur",
        "add": "Uygunluk Ekle",
        "view": "Eşleşmeleri Gör",
        "ai": "AI E-posta Asistanı",
        "hero": "Bitmeyen e-posta trafiği olmadan toplantı zamanı belirleyin.",
        "hero_sub": "Toplantı linki oluşturun, uygunlukları toplayın, ortak saatleri bulun ve profesyonel takip e-postası üretin.",
        "create_header": "Toplantı Oluştur",
        "create_help": "Yeni bir toplantı oluşturun. Platform otomatik Meeting Code ve paylaşım linki üretecek.",
        "add_header": "Uygunluk Ekle",
        "add_help": "Toplantı linkini açın veya Meeting Code’u manuel girin, sonra uygunluğunuzu ekleyin.",
        "view_header": "Ortak Saatleri Gör",
        "view_help": "Tüm uygunlukları inceleyin ve çakışan ortak zaman aralıklarını bulun.",
        "ai_header": "AI E-posta Asistanı",
        "ai_help": "Eşleşen saatlerden profesyonel toplantı e-postası oluşturun.",
        "meeting_code": "Meeting Code",
        "meeting_link": "Paylaşılabilir Toplantı Linki",
        "meeting_title": "Toplantı Başlığı",
        "meeting_placeholder": "EIC Pathfinder İş Birliği Toplantısı",
        "create_button": "Toplantı Linki Oluştur",
        "created_success": "Toplantı linki başarıyla oluşturuldu.",
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
        "name_warning": "Lütfen adınızı girin.",
        "code_warning": "Lütfen Meeting Code girin.",
        "time_warning": "Bitiş saati başlangıç saatinden sonra olmalıdır.",
        "saved": "Uygunluk başarıyla kaydedildi.",
        "all_availability": "Tüm Uygunluklar",
        "matching_slots": "Ortak Uygun Saatler",
        "matches_found": "Ortak uygun saat bulundu.",
        "no_matches": "Henüz ortak uygun saat bulunamadı.",
        "no_data": "Bu Meeting Code için henüz uygunluk eklenmemiş.",
        "meeting_not_found": "Toplantı bulunamadı. Lütfen Meeting Code’u kontrol edin.",
        "generate_email": "Profesyonel E-posta Oluştur",
        "generated_email": "Oluşturulan E-posta",
        "email_body": "E-posta Metni",
        "total_entries": "Uygunluk Kaydı",
        "total_matches": "Ortak Saat",
        "participants": "Kişi",
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

# Yardımcı fonksiyonlar
def get_base_url():
    try:
        return st.query_params.get("base_url", "https://your-app-url.streamlit.app")
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

def step_card(title, text):
    st.markdown(
        f"""
        <div class="step-card">
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
            <h4>📭</h4>
            <p>{message}</p>
        </div>
        """,
        unsafe_allow_html=True
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

# Yan panel ve dil seçimi
language = st.sidebar.selectbox(
    "Platform Language / Platform Dili",
    ["English", "Türkçe"]
)

t = TEXT[language]

query_meeting_code = get_query_meeting_code()

st.sidebar.markdown("### 📅 MeetAlign")

default_menu_index = 1 if query_meeting_code else 0

menu = st.sidebar.radio(
    t["menu"],
    [t["create"], t["add"], t["view"], t["ai"]],
    index=default_menu_index
)

# Ana başlık ve açıklama kartı
st.markdown(
    f"""
    <div class="hero-card">
        <div class="main-title">📅 {t["title"]}</div>
        <div class="subtitle">{t["caption"]}</div>
        <h3>{t["hero"]}</h3>
        <p class="small-muted">{t["hero_sub"]}</p>
    </div>
    """,
    unsafe_allow_html=True
)

# "Create Meeting" (Toplantı Oluşturma) Bölümü
if menu == t["create"]:
    st.header(t["create_header"])
    step_card("Step 1 / Adım 1", t["create_help"])

    section_open()
    meeting_title = st.text_input(
        t["meeting_title"],
        placeholder=t["meeting_placeholder"]
    )

    if st.button(t["create_button"], use_container_width=True):
        if meeting_title:
            meeting_code = create_meeting(meeting_title)
            base_url = get_base_url()
            meeting_link = f"{base_url}?meeting={meeting_code}"

            st.success(t["created_success"])

            c1, c2 = st.columns(2)

            with c1:
                st.text_input(t["meeting_code"], value=meeting_code, disabled=True)

            with c2:
                st.text_input(t["meeting_link"], value=meeting_link, disabled=True)

            st.write(t["copy_message"])
            st.code(
                f"""Hello,

Please add your availability for our meeting using the link below:

{meeting_link}

Meeting Code: {meeting_code}

Best regards"""
            )

            # Meeting Code'u URL’ye ekle
            set_meeting_query(meeting_code)

        else:
            st.warning(t["fill_title"])
    section_close()

# "Add Availability" (Uygunluk Ekleme) Bölümü
elif menu == t["add"]:
    st.header(t["add_header"])
    step_card("Step 2 / Adım 2", t["add_help"])

    section_open()

    default_code = query_meeting_code if query_meeting_code else ""

    meeting_code = st.text_input(
        t["meeting_code"],
        value=default_code,
        placeholder="AB12CD34"
    ).strip().upper()

    meeting = get_meeting(meeting_code) if meeting_code else None

    if meeting_code and meeting:
        st.success(f"{meeting[1]}")

    elif meeting_code and not meeting:
        st.warning(t["meeting_not_found"])

    c1, c2 = st.columns(2)

    with c1:
        name = st.text_input(t["your_name"])
        email = st.text_input(t["your_email"])

    with c2:
        role_label = st.selectbox(t["role"], [t["organizer"], t["participant"]])
        date = st.date_input(t["date"])

        time_c1, time_c2 = st.columns(2)

        with time_c1:
            start_time = st.time_input(t["start"])

        with time_c2:
            end_time = st.time_input(t["end"])

    if st.button(t["save"], use_container_width=True):
        if not meeting_code:
            st.warning(t["code_warning"])
        elif not name:
            st.warning(t["name_warning"])
        elif start_time >= end_time:
            st.warning(t["time_warning"])
        elif not get_meeting(meeting_code):
            st.warning(t["meeting_not_found"])
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

# "View Matches" (Eşleşmeleri Görüntüleme) Bölümü
elif menu == t["view"]:
    st.header(t["view_header"])
    step_card("Step 3 / Adım 3", t["view_help"])

    # Toplantı kodu giriş alanı
    default_code = query_meeting_code if query_meeting_code else ""

    meeting_code = st.text_input(
        t["meeting_code"],
        value=default_code,
        key="view_meeting_code"
    ).strip().upper()

    if meeting_code:
        meeting = get_meeting(meeting_code)

        if meeting:
            st.success(meeting[1])

        # Uygunluk verilerini al
        df = get_availability_dataframe(meeting_code, t)

        if not df.empty:
            matches = calculate_matches(df, t)

            # Metrik kartları göster
            m1, m2, m3 = st.columns(3)

            with m1:
                metric_card(len(df), t["total_entries"])

            with m2:
                metric_card(len(matches), t["total_matches"])

            with m3:
                metric_card(df[t["col_email"]].nunique(), t["participants"])

            # Tüm Uygunluklar bölümü
            section_open()
            st.subheader(t["all_availability"])
            st.dataframe(df, use_container_width=True, hide_index=True)
            section_close()

            # Eşleşen zaman dilimleri bölümü
            section_open()
            st.subheader(t["matching_slots"])

            if matches:
                st.success(t["matches_found"])
                st.dataframe(
                    pd.DataFrame(matches),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning(t["no_matches"])

            section_close()

        else:
            empty_state(t["no_data"])
    else:
        empty_state(t["code_warning"])

# "AI Email Assistant" (AI E-posta Asistanı) Bölümü
elif menu == t["ai"]:
    st.header(t["ai_header"])
    step_card("Step 4 / Adım 4", t["ai_help"])

    section_open()

    default_code = query_meeting_code if query_meeting_code else ""

    meeting_code = st.text_input(
        t["meeting_code"],
        value=default_code,
        key="ai_meeting_code"
    ).strip().upper()

    meeting = get_meeting(meeting_code) if meeting_code else None

    if meeting:
        default_title = meeting[1]
    else:
        default_title = t["meeting_placeholder"]

    meeting_title = st.text_input(
        t["meeting_title"],
        value=default_title
    )

    section_close()

    if meeting_code:
        df = get_availability_dataframe(meeting_code, t)

        if not df.empty:
            matches = calculate_matches(df, t)

            if matches:
                section_open()
                st.subheader(t["matching_slots"])
                st.dataframe(
                    pd.DataFrame(matches),
                    use_container_width=True,
                    hide_index=True
                )

                if st.button(t["generate_email"], use_container_width=True):
                    normalized_matches = []

                    for item in matches:
                        normalized_matches.append({
                            "Date": item[t["col_date"]],
                            "Available From": item[t["col_from"]],
                            "Available Until": item[t["col_until"]],
                        })

                    # OpenRouter API üzerinden profesyonel e-posta oluştur
                    email_text = generate_meeting_email(
                        meeting_title,
                        normalized_matches,
                        language=language
                    )

                    st.subheader(t["generated_email"])
                    st.text_area(
                        t["email_body"],
                        value=email_text,
                        height=300
                    )

                section_close()
            else:
                empty_state(t["no_matches"])
        else:
            empty_state(t["no_data"])
    else:
        empty_state(t["code_warning"])

# Geçici Test Butonu (OpenRouter API Bağlantı Testi)
st.sidebar.markdown("---")
st.sidebar.markdown("### Debug")
if st.sidebar.button("Test OpenRouter Connection"):
    test_result = test_openrouter_connection()
    st.sidebar.write(test_result)
