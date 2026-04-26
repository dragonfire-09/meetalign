import streamlit as st
import pandas as pd
from database import init_db, add_availability, get_availability
from ai_assistant import generate_meeting_email

init_db()

st.set_page_config(
    page_title="MeetAlign",
    page_icon="📅",
    layout="wide"
)

TEXT = {
    "English": {
        "title": "📅 MeetAlign",
        "caption": "Smart meeting availability tool for project teams",
        "welcome": "Welcome to **MeetAlign**. This tool helps people find a common meeting time.",
        "language": "Platform Language",
        "menu": "Menu",
        "create": "Create Meeting",
        "add": "Add Availability",
        "view": "View Matches",
        "ai": "AI Email Assistant",

        "create_header": "Create Meeting",
        "create_help": """
Step 1: Create a meeting.

1. Enter a meeting title.
2. Choose or keep the Meeting ID.
3. Click **Create Meeting**.
4. Share this Meeting ID with the other person.
""",
        "meeting_id": "Meeting ID",
        "choose_meeting_id": "Choose Meeting ID",
        "meeting_title": "Meeting Title",
        "meeting_placeholder": "EIC Pathfinder Collaboration Meeting",
        "create_button": "Create Meeting",
        "created_success": "Meeting created successfully.",
        "share_id": "Share this Meeting ID:",
        "example_message": "Example message:",
        "fill_title": "Please enter a meeting title.",

        "add_header": "Add Availability",
        "add_help": """
Step 2: Add your availability.

1. Enter the Meeting ID you received.
2. Write your name and email.
3. Select your role.
4. Choose the date and available time range.
5. Click **Save Availability**.
""",
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
        "time_warning": "End time must be later than start time.",
        "saved": "Availability saved successfully.",

        "view_header": "View Matches",
        "view_help": """
Step 3: View matching time slots.

1. Enter the Meeting ID.
2. The system will show all submitted availability.
3. If both sides selected overlapping times, the matching slots will appear below.
4. Use one of the matching slots to confirm the meeting.
""",
        "all_availability": "All Availability",
        "matching_slots": "Matching Time Slots",
        "matches_found": "Matching slots found.",
        "no_matches": "No matching time slots found yet.",
        "no_data": "No availability has been added for this meeting yet.",

        "ai_header": "AI Email Assistant",
        "ai_help": """
Step 4: Generate a professional email.

1. Enter the Meeting ID.
2. Check the matching time slots.
3. Click **Generate Professional Email**.
4. Copy the generated email and send it to the participant.
""",
        "generate_email": "Generate Professional Email",
        "generated_email": "Generated Email",
        "email_body": "Email Body",

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
        "title": "📅 MeetAlign",
        "caption": "Proje ekipleri için akıllı toplantı uygunluk aracı",
        "welcome": "**MeetAlign**’a hoş geldiniz. Bu araç, iki veya daha fazla kişinin ortak toplantı zamanı bulmasına yardımcı olur.",
        "language": "Platform Dili",
        "menu": "Menü",
        "create": "Toplantı Oluştur",
        "add": "Uygunluk Ekle",
        "view": "Eşleşmeleri Gör",
        "ai": "AI E-posta Asistanı",

        "create_header": "Toplantı Oluştur",
        "create_help": """
Adım 1: Toplantı oluşturun.

1. Toplantı başlığını yazın.
2. Meeting ID’yi seçin veya mevcut değeri kullanın.
3. **Toplantı Oluştur** butonuna basın.
4. Bu Meeting ID’yi karşı tarafla paylaşın.
""",
        "meeting_id": "Meeting ID",
        "choose_meeting_id": "Meeting ID Seç",
        "meeting_title": "Toplantı Başlığı",
        "meeting_placeholder": "EIC Pathfinder İş Birliği Toplantısı",
        "create_button": "Toplantı Oluştur",
        "created_success": "Toplantı başarıyla oluşturuldu.",
        "share_id": "Bu Meeting ID’yi paylaşın:",
        "example_message": "Örnek mesaj:",
        "fill_title": "Lütfen toplantı başlığı girin.",

        "add_header": "Uygunluk Ekle",
        "add_help": """
Adım 2: Uygun olduğunuz zamanı ekleyin.

1. Size verilen Meeting ID’yi girin.
2. Adınızı ve e-posta adresinizi yazın.
3. Rolünüzü seçin.
4. Uygun olduğunuz tarih ve saat aralığını girin.
5. **Uygunluk Kaydet** butonuna basın.
""",
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
        "time_warning": "Bitiş saati başlangıç saatinden sonra olmalıdır.",
        "saved": "Uygunluk başarıyla kaydedildi.",

        "view_header": "Eşleşmeleri Gör",
        "view_help": """
Adım 3: Ortak uygun saatleri görün.

1. Meeting ID’yi girin.
2. Sistem girilen tüm uygunlukları gösterecek.
3. İki tarafın saatleri çakışıyorsa ortak zamanlar aşağıda listelenecek.
4. Bu ortak zamanlardan birini toplantı için onaylayabilirsiniz.
""",
        "all_availability": "Tüm Uygunluklar",
        "matching_slots": "Ortak Uygun Saatler",
        "matches_found": "Ortak uygun saat bulundu.",
        "no_matches": "Henüz ortak uygun saat bulunamadı.",
        "no_data": "Bu Meeting ID için henüz uygunluk eklenmemiş.",

        "ai_header": "AI E-posta Asistanı",
        "ai_help": """
Adım 4: Profesyonel e-posta oluşturun.

1. Meeting ID’yi girin.
2. Ortak uygun saatleri kontrol edin.
3. **Profesyonel E-posta Oluştur** butonuna basın.
4. Oluşan e-postayı kopyalayıp karşı tarafa gönderin.
""",
        "generate_email": "Profesyonel E-posta Oluştur",
        "generated_email": "Oluşturulan E-posta",
        "email_body": "E-posta Metni",

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


def get_availability_dataframe(meeting_id, t):
    rows = get_availability(meeting_id)

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


language = st.sidebar.selectbox(
    "Platform Language / Platform Dili",
    ["English", "Türkçe"]
)

t = TEXT[language]

st.title(t["title"])
st.caption(t["caption"])
st.markdown(t["welcome"])

menu = st.sidebar.radio(
    t["menu"],
    [t["create"], t["add"], t["view"], t["ai"]]
)


if menu == t["create"]:
    st.header(t["create_header"])
    st.info(t["create_help"])

    meeting_id = st.number_input(
        t["choose_meeting_id"],
        min_value=1,
        step=1
    )

    meeting_title = st.text_input(
        t["meeting_title"],
        placeholder=t["meeting_placeholder"]
    )

    if st.button(t["create_button"]):
        if meeting_title:
            st.success(t["created_success"])
            st.info(f"{t['share_id']} {meeting_id}")
            st.write(t["example_message"])
            st.code(
                f"Please add your availability for our meeting using Meeting ID: {meeting_id}"
            )
        else:
            st.warning(t["fill_title"])


elif menu == t["add"]:
    st.header(t["add_header"])
    st.info(t["add_help"])

    meeting_id = st.number_input(
        t["meeting_id"],
        min_value=1,
        step=1
    )

    name = st.text_input(t["your_name"])
    email = st.text_input(t["your_email"])

    role_label = st.selectbox(
        t["role"],
        [t["organizer"], t["participant"]]
    )

    date = st.date_input(t["date"])
    start_time = st.time_input(t["start"])
    end_time = st.time_input(t["end"])

    if st.button(t["save"]):
        if not name:
            st.warning(t["name_warning"])
        elif start_time >= end_time:
            st.warning(t["time_warning"])
        else:
            add_availability(
                meeting_id,
                name,
                email,
                role_label,
                date,
                start_time,
                end_time
            )
            st.success(t["saved"])


elif menu == t["view"]:
    st.header(t["view_header"])
    st.info(t["view_help"])

    meeting_id = st.number_input(
        t["meeting_id"],
        min_value=1,
        step=1,
        key="match_meeting_id"
    )

    df = get_availability_dataframe(meeting_id, t)

    if not df.empty:
        st.subheader(t["all_availability"])
        st.dataframe(df, use_container_width=True, hide_index=True)

        matches = calculate_matches(df, t)

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
    else:
        st.info(t["no_data"])


elif menu == t["ai"]:
    st.header(t["ai_header"])
    st.info(t["ai_help"])

    meeting_id = st.number_input(
        t["meeting_id"],
        min_value=1,
        step=1,
        key="ai_meeting_id"
    )

    meeting_title = st.text_input(
        t["meeting_title"],
        value=t["meeting_placeholder"]
    )

    df = get_availability_dataframe(meeting_id, t)

    if not df.empty:
        matches = calculate_matches(df, t)

        if matches:
            st.subheader(t["matching_slots"])
            st.dataframe(
                pd.DataFrame(matches),
                use_container_width=True,
                hide_index=True
            )

            if st.button(t["generate_email"]):
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
                    height=300
                )
        else:
            st.warning(t["no_matches"])
    else:
        st.info(t["no_data"])
