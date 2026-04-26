
import streamlit as st
import pandas as pd
import base64
from database import (
    init_db,
    create_meeting,
    get_meeting,
    add_availability,
    get_availability
)
from ai_assistant import generate_meeting_email, ai_chatbot_response 
from datetime import datetime
import uuid

# Veritabanını başlat
init_db()

# Sayfa yapılandırması
st.set_page_config(
    page_title="MeetAlign",
    page_icon="📅",
    layout="wide"
)

# Stiller
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(180deg, #f0f4f8 0%, #e0e7ff 100%);
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
        .confirm-card {
            background: #eff6ff;
            padding: 22px;
            border-radius: 16px;
            border: 1px solid #bfdbfe;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
            margin-top: 18px;
            text-align: center;
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
        .chat-bubble {
            background: #e0e7ff;
            padding: 14px;
            border-radius: 12px;
            margin-bottom: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# Metinler
TEXT = {
    "English": {
        "title": "MeetAlign",
        "caption": "Smart meeting availability platform for project teams, researchers and consortium partners.",
        "menu": "Workspace",
        "create": "Create Meeting",
        "add": "Add Availability",
        "view": "View Matches",
        "ai": "AI Email Assistant",
        "chat": "AI Chatbot",
        "confirm": "Confirm Meeting",
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
        "chat_header": "AI Chatbot",
        "chat_help": "Ask questions or get assistance from the AI chatbot.",
        "confirm_header": "Confirm Meeting Slot",
        "confirm_help": "Select a matching slot to confirm the meeting and generate a calendar invitation.",
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
        "confirm_button": "Confirm This Slot",
        "confirmed_success": "Meeting confirmed successfully!",
        "ics_download": "Download .ics File",
        "ics_help": "Download and share the calendar invite with participants.",
    },
    "Türkçe": {
        "title": "MeetAlign",
        "caption": "Proje ekipleri, araştırmacılar ve konsorsiyum ortakları için akıllı toplantı planlama platformu.",
        "menu": "Çalışma Alanı",
        "create": "Toplantı Oluştur",
        "add": "Uygunluk Ekle",
        "view": "Eşleşmeleri Gör",
        "ai": "AI E-posta Asistanı",
        "chat": "AI Sohbet Asistanı",
        "confirm": "Toplantıyı Onayla",
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
        "chat_header": "AI Sohbet Asistanı",
        "chat_help": "AI sohbet asistanına sorular sorun veya yardım alın.",
        "confirm_header": "Toplantı Saatini Onayla",
        "confirm_help": "Eşleşen saatlerden birini seçin ve toplantıyı onaylayın, takvim daveti oluşturun.",
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
        "confirm_button": "Bu Saati Onayla",
        "confirmed_success": "Toplantı başarıyla onaylandı!",
        "ics_download": ".ics Dosyasını İndir",
        "ics_help": "Takvim davetini indir ve katılımcılarla paylaş.",
    }
}

# Temel fonksiyonlar
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


def confirm_card(message):
    st.markdown(
        f"""
        <div class="confirm-card">
            <h4>✅</h4>
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


def generate_ics(meeting_title, confirmed_slot, organizer_email):
    from ics import Calendar, Event
    c = Calendar()
    e = Event()
    e.name = meeting_title
    e.begin = datetime.combine(confirmed_slot['date'], confirmed_slot['from'])
    e.end = datetime.combine(confirmed_slot['date'], confirmed_slot['until'])
    e.description = f"Confirmed meeting with {confirmed_slot['organizer']} and {confirmed_slot['participant']}."
    e.organizer = f"mailto:{organizer_email}"
    c.events.add(e)
    return str(c)




# Kullanıcı dili seçimi
language = st.sidebar.selectbox(
    "Platform Language / Platform Dili",
    ["English", "Türkçe"]
)

# Seçilen dilin metinlerini yükle
t = TEXT[language]

# URL Query’den Meeting Code’u al
query_meeting_code = get_query_meeting_code()

# Sidebar başlık
st.sidebar.markdown("### 📅 MeetAlign")

# Varsayılan menü indeksi (Query parametresine göre “Add” adımına yönlendirme)
default_menu_index = 1 if query_meeting_code else 0

# Menü seçenekleri
menu = st.sidebar.radio(
    t["menu"],
    [t["create"], t["add"], t["view"], t["ai"], t["chat"], t["confirm"]],
    index=default_menu_index
)

# Hero bölümü (Başlık kartı)
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


# “Create Meeting” (Toplantı Oluştur) Adımı
if menu == t["create"]:
    st.header(t["create_header"])
    step_card("Step 1 / Adım 1", t["create_help"])

    section_open()

    # Toplantı başlığı girişi
    meeting_title = st.text_input(
        t["meeting_title"],
        placeholder=t["meeting_placeholder"]
    )

    # Toplantı oluşturma butonu
    if st.button(t["create_button"], use_container_width=True):
        if meeting_title:
            # Toplantı kodu oluştur
            meeting_code = create_meeting(meeting_title)
            meeting_link = f"{get_base_url()}?meeting={meeting_code}"

            # Başarı mesajı
            st.success(t["created_success"])

            # Meeting Code ve Link gösterimi
            c1, c2 = st.columns(2)
            with c1:
                st.text_input(t["meeting_code"], value=meeting_code)
            with c2:
                st.text_input(t["meeting_link"], value=meeting_link)

            # Davet mesajını gösterme ve kopyalama
            st.write(t["copy_message"])
            st.code(
                f"""Hello,

Please add your availability for our meeting using the link below:

{meeting_link}

Meeting Code: {meeting_code}

Best regards""",
                language="text"
            )

            # URL Query parametresine Meeting Code’u ayarla (kullanıcı diğer adımlara geçince otomatik dolacak)
            set_meeting_query(meeting_code)

        else:
            st.warning(t["fill_title"])

    section_close()


# “Add Availability” (Uygunluk Ekle) Adımı
elif menu == t["add"]:
    st.header(t["add_header"])
    step_card("Step 2 / Adım 2", t["add_help"])

    section_open()

    # Meeting Code giriş alanı (Query’den otomatik gelebilir)
    default_code = query_meeting_code if query_meeting_code else ""
    meeting_code = st.text_input(
        t["meeting_code"],
        value=default_code,
        placeholder="AB12CD34"
    ).strip().upper()

    # Meeting Code geçerliyse toplantı bilgilerini çek
    meeting = get_meeting(meeting_code) if meeting_code else None

    # Toplantı adı gösterimi
    if meeting_code and meeting:
        st.success(f"{meeting[1]}")
    elif meeting_code and not meeting:
        st.warning(t["meeting_not_found"])

    # Kullanıcı uygunluk bilgisi formu
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

    # Uygunluk kaydetme butonu
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


# “View Matches” (Eşleşmeleri Görüntüle) Adımı
elif menu == t["view"]:
    st.header(t["view_header"])
    step_card("Step 3 / Adım 3", t["view_help"])

    # Meeting Code giriş
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

        # Uygunluk verisini çek
        df = get_availability_dataframe(meeting_code, t)

        if not df.empty:
            matches = calculate_matches(df, t)

            # Metrics kartlar: Toplam kayıt, eşleşen saatler, katılımcı sayısı
            m1, m2, m3 = st.columns(3)
            with m1:
                metric_card(len(df), t["total_entries"])
            with m2:
                metric_card(len(matches), t["total_matches"])
            with m3:
                metric_card(df[t["col_email"]].nunique(), t["participants"])

            # Tüm uygunlukları göster
            section_open()
            st.subheader(t["all_availability"])
            st.dataframe(df, use_container_width=True, hide_index=True)
            section_close()

            # Eşleşen zaman dilimlerini göster
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


# “AI Email Assistant” (AI E-posta Asistanı) Adımı
elif menu == t["ai"]:
    st.header(t["ai_header"])
    step_card("Step 4 / Adım 4", t["ai_help"])

    section_open()

    # Meeting Code giriş
    default_code = query_meeting_code if query_meeting_code else ""
    meeting_code = st.text_input(
        t["meeting_code"],
        value=default_code,
        key="ai_meeting_code"
    ).strip().upper()

    # Toplantı başlığı
    meeting = get_meeting(meeting_code) if meeting_code else None
    default_title = meeting[1] if meeting else t["meeting_placeholder"]
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

                # AI E-posta oluşturma butonu
                if st.button(t["generate_email"], use_container_width=True):
                    normalized_matches = []
                    for item in matches:
                        normalized_matches.append({
                            "Date": item[t["col_date"]],
                            "Available From": item[t["col_from"]],
                            "Available Until": item[t["col_until"]],
                        })

                    # AI ile e-posta metni oluştur
                    email_text = generate_meeting_email(
                        meeting_title,
                        normalized_matches
                    )

                    # Oluşturulan E-posta Metni
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


# “AI Chatbot” (AI Sohbet Asistanı) Adımı
elif menu == t["chat"]:
    st.header(t["chat_header"])
    step_card("Step 5 / Adım 5", t["chat_help"])

    section_open()

    # Chat geçmişi oturum durumunda tutma
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Chat geçmişini göster (Mesaj balonları)
    for chat in st.session_state["chat_history"]:
        if chat["from"] == "user":
            st.markdown(
                f"<div class='chat-bubble' style='background: #dbeafe; text-align: right;'>{chat['message']}</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='chat-bubble' style='background: #e0e7ff; text-align: left;'>{chat['message']}</div>",
                unsafe_allow_html=True
            )

    # Kullanıcı mesaj girişi
    user_message = st.text_input(
        "Message / Mesaj",
        key="user_chat_message"
    )

    # Mesaj gönderildiğinde işleme
    if st.button("Send / Gönder", key="send_chat_message"):
        if user_message:
            # Kullanıcı mesajını geçmişe ekle
            st.session_state["chat_history"].append({
                "from": "user",
                "message": user_message
            })

            # AI Chatbot cevabı al
            bot_response = ai_chatbot_response(user_message, language)

            # Bot cevabını geçmişe ekle
            st.session_state["chat_history"].append({
                "from": "bot",
                "message": bot_response
            })

            # Sayfayı yeniden yükleyerek sohbeti güncelle
            st.experimental_rerun()

    section_close()


# “Confirm Meeting” (Toplantıyı Onayla) Adımı
elif menu == t["confirm"]:
    st.header(t["confirm_header"])
    step_card("Step 6 / Adım 6", t["confirm_help"])

    section_open()

    # Meeting Code giriş
    default_code = query_meeting_code if query_meeting_code else ""
    meeting_code = st.text_input(
        t["meeting_code"],
        value=default_code,
        key="confirm_meeting_code"
    ).strip().upper()

    # Toplantı başlığı belirleme
    meeting = get_meeting(meeting_code) if meeting_code else None
    default_title = meeting[1] if meeting else t["meeting_placeholder"]
    meeting_title = st.text_input(
        t["meeting_title"],
        value=default_title,
        key="confirm_meeting_title"
    )

    if meeting_code:
        df = get_availability_dataframe(meeting_code, t)

        if not df.empty:
            matches = calculate_matches(df, t)

            if matches:
                # Eşleşen zaman dilimlerini seçenek olarak sun
                st.subheader(t["matching_slots"])
                selected_match = st.selectbox(
                    t["matching_slots"],
                    matches,
                    format_func=lambda x: f"{x[t['col_date']]}: {x[t['col_from']]} - {x[t['col_until']]}"
                )

                # Onaylama butonu
                if st.button(t["confirm_button"], use_container_width=True):
                    # Onaylanan toplantı detayları
                    confirmed_slot = {
                        "date": selected_match[t["col_date"]],
                        "from": selected_match[t["col_from"]],
                        "until": selected_match[t["col_until"]],
                        "organizer": selected_match[t["organizer"]],
                        "participant": selected_match[t["participant"]]
                    }

                    # Organizer e-posta adresini bul (örnek bir yöntem)
                    organizer_email = df[
                        (df[t["col_name"]] == confirmed_slot["organizer"])
                        & (df[t["col_role"]] == t["organizer"])
                    ][t["col_email"]].values[0]

                    # Başarı mesajı göster
                    confirm_card(t["confirmed_success"])

                    # .ics dosyası oluştur
                    ics_content = generate_ics(meeting_title, confirmed_slot, organizer_email)

                    # .ics dosyasını indirme linki
                    b64 = base64.b64encode(ics_content.encode()).decode()
                    href = f'<a href="data:text/calendar;base64,{b64}" download="{meeting_code}.ics">{t["ics_download"]}</a>'
                    st.markdown(href, unsafe_allow_html=True)

                    st.info(t["ics_help"])

            else:
                empty_state(t["no_matches"])
        else:
            empty_state(t["no_data"])
    else:
        empty_state(t["code_warning"])

    section_close()
