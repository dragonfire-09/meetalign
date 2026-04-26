import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from database import (
    init_db,
    create_meeting,
    get_meeting,
    add_availability,
    get_availability,
    cancel_meeting,
    archive_meeting,
    restore_meeting,
    confirm_meeting_slot,
    get_meeting_history,
    get_all_meetings
)
from ai_assistant import parse_meeting_command, generate_meeting_email, ai_chatbot_response

init_db()

st.set_page_config(
    page_title="MeetAlign",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ──────────────────────────────────────────────
st.markdown("""
<style>
    .stApp{background:linear-gradient(180deg,#f8fafc 0%,#eef2ff 100%)}
    section[data-testid="stSidebar"]{background:#fff;border-right:1px solid #e5e7eb}
    .hero{background:#fff;padding:30px;border-radius:26px;border:1px solid #e5e7eb;
          box-shadow:0 18px 45px rgba(15,23,42,.08);margin-bottom:24px}
    .hero-title{font-size:42px;font-weight:850;color:#111827;margin-bottom:8px}
    .hero-sub{color:#6b7280;font-size:17px}
    .card{background:#fff;padding:24px;border-radius:22px;border:1px solid #e5e7eb;
          box-shadow:0 10px 30px rgba(15,23,42,.06);margin-top:18px;margin-bottom:18px}
    .guide{background:#f8fafc;padding:16px 18px;border-radius:16px;border:1px solid #e5e7eb;
           color:#475569;margin-bottom:18px}
    .pill{display:inline-block;padding:7px 12px;background:#eff6ff;color:#1d4ed8;
          border-radius:999px;font-size:13px;font-weight:700;margin-right:8px;border:1px solid #bfdbfe}
    .empty{background:#fff;padding:28px;border-radius:22px;border:1px dashed #cbd5e1;
           text-align:center;color:#64748b;margin-top:18px}
    .status-active{color:#16a34a;font-weight:700}
    .status-cancelled{color:#dc2626;font-weight:700}
    .status-archived{color:#9ca3af;font-weight:700}
    .status-confirmed{color:#2563eb;font-weight:700}
    .history-row{padding:8px 12px;border-left:3px solid #2563eb;margin-bottom:6px;
                 background:#f8fafc;border-radius:0 8px 8px 0;font-size:14px}
    div.stButton>button{background:linear-gradient(90deg,#2563eb,#4f46e5);color:#fff;
        border:none;border-radius:14px;padding:.75rem 1.25rem;font-weight:750;
        box-shadow:0 10px 24px rgba(37,99,235,.28)}
    div.stButton>button:hover{background:linear-gradient(90deg,#1d4ed8,#4338ca);color:#fff;border:none}
</style>
""", unsafe_allow_html=True)

# ── TEXT ─────────────────────────────────────────────
TEXT = {
    "English": {
        "menu": "Workspace",
        "create": "Create Meeting",
        "availability": "Add Availability",
        "confirm": "Confirm & Calendar",
        "chatbot": "AI Chatbot",
        "manage": "Manage Meetings",
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
        "already_confirmed": "This meeting is already confirmed.",
        "download_ics": "Download .ics Calendar Invite",
        "google_meet": "Google Meet",
        "google_coming": "Coming Soon — Connect Google Calendar to generate Google Meet links automatically.",
        "send_email": "Send Confirmation Email",
        "recipient_email": "Recipient Email",
        "email_sent": "Confirmation email sent.",
        "email_failed": "Email could not be sent.",
        "cancel": "Cancel Meeting",
        "cancelled": "Meeting cancelled.",
        "cancelled_warning": "This meeting has been cancelled. You cannot add availability.",
        "archive": "Archive Meeting",
        "archived": "Meeting archived.",
        "archived_warning": "This meeting has been archived.",
        "restore": "Restore Meeting",
        "restored": "Meeting restored to active.",
        "history": "Meeting History",
        "no_history": "No history found.",
        "status": "Status",
        "all_meetings": "All Meetings",
        "no_meetings": "No meetings found.",
        "generate_email": "Generate AI Email",
        "generated_email": "Generated Email",
        "chat_help": "Example: Plan a meeting with Moshira on 2026-05-12 at 14:00 for EIC Pathfinder.",
        "chat_input": "Write your meeting request or ask a question",
        "chat_button": "Send",
        "parsed": "AI understood this:",
        "chat_mode": "Chat Mode",
        "mode_command": "Create Meeting from Text",
        "mode_chat": "Free Chat",
    },
    "Türkçe": {
        "menu": "Çalışma Alanı",
        "create": "Toplantı Oluştur",
        "availability": "Uygunluk Ekle",
        "confirm": "Onayla & Takvim",
        "chatbot": "AI Chatbot",
        "manage": "Toplantı Yönetimi",
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
        "already_confirmed": "Bu toplantı zaten onaylanmış.",
        "download_ics": ".ics Takvim Daveti İndir",
        "google_meet": "Google Meet",
        "google_coming": "Yakında — Google Calendar bağlandığında Google Meet linki otomatik üretilecek.",
        "send_email": "Onay E-postası Gönder",
        "recipient_email": "Alıcı E-posta",
        "email_sent": "Onay e-postası gönderildi.",
        "email_failed": "E-posta gönderilemedi.",
        "cancel": "Toplantıyı İptal Et",
        "cancelled": "Toplantı iptal edildi.",
        "cancelled_warning": "Bu toplantı iptal edilmiştir. Uygunluk ekleyemezsiniz.",
        "archive": "Toplantıyı Arşivle",
        "archived": "Toplantı arşivlendi.",
        "archived_warning": "Bu toplantı arşivlenmiştir.",
        "restore": "Toplantıyı Geri Al",
        "restored": "Toplantı aktif duruma getirildi.",
        "history": "Toplantı Geçmişi",
        "no_history": "Geçmiş bulunamadı.",
        "status": "Durum",
        "all_meetings": "Tüm Toplantılar",
        "no_meetings": "Toplantı bulunamadı.",
        "generate_email": "AI E-posta Oluştur",
        "generated_email": "Oluşturulan E-posta",
        "chat_help": "Örnek: 12 Mayıs 2026 saat 14:00'te Moshira ile EIC Pathfinder toplantısı planla.",
        "chat_input": "Toplantı isteğinizi yazın veya soru sorun",
        "chat_button": "Gönder",
        "parsed": "AI bunu anladı:",
        "chat_mode": "Sohbet Modu",
        "mode_command": "Metinden Toplantı Oluştur",
        "mode_chat": "Serbest Sohbet",
    }
}

# ── HELPERS ──────────────────────────────────────────
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

def card_open():
    st.markdown('<div class="card">', unsafe_allow_html=True)

def card_close():
    st.markdown('</div>', unsafe_allow_html=True)

def guide(text):
    st.markdown(f'<div class="guide">{text}</div>', unsafe_allow_html=True)

def empty(msg):
    st.markdown(f'<div class="empty"><h3>📭</h3><p>{msg}</p></div>', unsafe_allow_html=True)

def status_badge(status):
    css_class = f"status-{status}"
    label = status.upper()
    return f'<span class="{css_class}">{label}</span>'

def get_df(meeting_code):
    rows = get_availability(meeting_code)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows, columns=["Name", "Email", "Role", "Date", "Start Time", "End Time"])

def calc_matches(df, org_label, part_label):
    orgs = df[df["Role"] == org_label]
    parts = df[df["Role"] == part_label]
    matches = []
    for _, o in orgs.iterrows():
        for _, p in parts.iterrows():
            if o["Date"] == p["Date"]:
                s = max(o["Start Time"], p["Start Time"])
                e = min(o["End Time"], p["End Time"])
                if s < e:
                    matches.append({
                        "Date": o["Date"],
                        "Start": s,
                        "End": e,
                        "Organizer": o["Name"],
                        "Participant": p["Name"],
                        "Participant Email": p["Email"]
                    })
    return matches

def make_ics(title, date_str, start_str, end_str, description=""):
    start_str = str(start_str)
    end_str = str(end_str)
    if len(start_str) == 5:
        start_str += ":00"
    if len(end_str) == 5:
        end_str += ":00"
    s = datetime.strptime(f"{date_str} {start_str}", "%Y-%m-%d %H:%M:%S")
    e = datetime.strptime(f"{date_str} {end_str}", "%Y-%m-%d %H:%M:%S")
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MeetAlign//EN
BEGIN:VEVENT
UID:{stamp}@meetalign
DTSTAMP:{stamp}
DTSTART:{s.strftime("%Y%m%dT%H%M%S")}
DTEND:{e.strftime("%Y%m%dT%H%M%S")}
SUMMARY:{title}
DESCRIPTION:{description}
END:VEVENT
END:VCALENDAR"""

def send_email(to, subject, body):
    api_key = st.secrets.get("RESEND_API_KEY", "")
    sender = st.secrets.get("SENDER_EMAIL", "")
    if not api_key or not sender:
        return False, "RESEND_API_KEY or SENDER_EMAIL missing in Streamlit Secrets."
    try:
        r = requests.post(
            "https://api.resend.com/emails",
            json={"from": sender, "to": [to], "subject": subject, "html": body.replace("\n", "<br>")},
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=30
        )
        if r.status_code in [200, 201, 202]:
            return True, r.text
        return False, r.text
    except Exception as ex:
        return False, str(ex)

def meeting_is_blocked(meeting, t):
    if not meeting:
        return True, t["not_found"]
    status = meeting[2]
    if status == "cancelled":
        return True, t["cancelled_warning"]
    if status == "archived":
        return True, t["archived_warning"]
    return False, ""

# ── SIDEBAR ──────────────────────────────────────────
language = st.sidebar.selectbox("Platform Language / Platform Dili", ["English", "Türkçe"])
t = TEXT[language]
query_code = get_query_code()
st.sidebar.markdown("### 📅 MeetAlign")
menu = st.sidebar.radio(
    t["menu"],
    [t["create"], t["availability"], t["confirm"], t["chatbot"], t["manage"]],
    index=1 if query_code else 0
)

# ── HERO ─────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
    <span class="pill">Availability</span>
    <span class="pill">Calendar Invite</span>
    <span class="pill">AI Chatbot</span>
    <span class="pill">Manage</span>
    <div class="hero-title">📅 {t["title"]}</div>
    <div class="hero-sub">{t["subtitle"]}</div>
    <h3>{t["hero"]}</h3>
</div>
""", unsafe_allow_html=True)

# ── CREATE MEETING ───────────────────────────────────
if menu == t["create"]:
    st.header(t["create"])
    guide("1. Enter a meeting title → 2. Create link → 3. Share with participants.")
    card_open()
    mt = st.text_input(t["meeting_title"], placeholder=t["meeting_placeholder"])
    if st.button(t["create_button"], use_container_width=True):
        if not mt:
            st.warning(t["meeting_title"])
        else:
            mc = create_meeting(mt)
            ml = f"{get_base_url()}?meeting={mc}"
            st.success(t["created"])
            c1, c2 = st.columns([1, 2])
            with c1:
                st.text_input(t["meeting_code"], value=mc)
            with c2:
                st.text_input(t["meeting_link"], value=ml)
            st.subheader(t["copy_invitation"])
            st.code(f"""Hello,

I created a meeting availability link for:
{mt}

Please add your availability:
{ml}

Meeting Code: {mc}

Best regards""")
    card_close()

# ── ADD AVAILABILITY ─────────────────────────────────
elif menu == t["availability"]:
    st.header(t["availability"])
    guide("1. Enter Meeting Code → 2. Fill your details → 3. Save.")
    card_open()
    mc = st.text_input(t["meeting_code"], value=query_code, placeholder="AB12CD34").strip().upper()
    meeting = get_meeting(mc) if mc else None

    if mc and not meeting:
        st.warning(t["not_found"])
    elif meeting:
        blocked, msg = meeting_is_blocked(meeting, t)
        if blocked:
            st.error(msg)
            card_close()
            st.stop()
        st.success(f"{meeting[1]}")
        st.markdown(f"{t['status']}: {status_badge(meeting[2])}", unsafe_allow_html=True)

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
        if not mc:
            st.warning(t["enter_code"])
        elif not get_meeting(mc):
            st.warning(t["not_found"])
        else:
            m = get_meeting(mc)
            blocked, msg = meeting_is_blocked(m, t)
            if blocked:
                st.error(msg)
            elif not name:
                st.warning(t["enter_name"])
            elif start_time >= end_time:
                st.warning(t["time_error"])
            else:
                add_availability(mc, name, email, role, date, start_time, end_time)
                st.success(t["saved"])
    card_close()

# ── CONFIRM & CALENDAR ──────────────────────────────
elif menu == t["confirm"]:
    st.header(t["confirm"])
    guide("1. Enter Meeting Code → 2. Select matching slot → 3. Confirm & download .ics or send email.")
    card_open()
    mc = st.text_input(t["meeting_code"], value=query_code, key="conf_code").strip().upper()
    meeting = get_meeting(mc) if mc else None

    if not mc:
        st.info(t["enter_code"])
        card_close()
        st.stop()
    if not meeting:
        st.warning(t["not_found"])
        card_close()
        st.stop()

    blocked, msg = meeting_is_blocked(meeting, t)
    mtitle = meeting[1]
    mstatus = meeting[2]

    st.success(mtitle)
    st.markdown(f"{t['status']}: {status_badge(mstatus)}", unsafe_allow_html=True)

    if mstatus == "confirmed":
        st.info(f"{t['already_confirmed']}: {meeting[3]} | {meeting[4]} - {meeting[5]}")
        ics = make_ics(mtitle, meeting[3], meeting[4], meeting[5],
                       description=f"Confirmed via MeetAlign. Code: {mc}")
        st.download_button(t["download_ics"], data=ics,
                           file_name=f"meetalign_{mc}.ics", mime="text/calendar",
                           use_container_width=True)

    if blocked and mstatus != "confirmed":
        st.error(msg)
        card_close()
        st.stop()

    df = get_df(mc)
    if df.empty:
        empty(t["no_data"])
        card_close()
        st.stop()

    st.subheader(t["all_availability"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    matches = calc_matches(df, t["organizer"], t["participant"])
    st.subheader(t["matches"])
    if not matches:
        empty(t["no_match"])
        card_close()
        st.stop()

    mdf = pd.DataFrame(matches)
    st.dataframe(mdf, use_container_width=True, hide_index=True)

    # AI Email
    if st.button(t["generate_email"], key="gen_email"):
        email_text = generate_meeting_email(mtitle, matches, language=language)
        st.subheader(t["generated_email"])
        st.text_area("", value=email_text, height=250)

    si = st.selectbox(
        t["select_slot"],
        range(len(matches)),
        format_func=lambda i: f"{matches[i]['Date']} | {matches[i]['Start']} - {matches[i]['End']}"
    )
    sel = matches[si]
    st.markdown(f"### ✅ Selected: **{sel['Date']}** | **{sel['Start']}** - **{sel['End']}**")

    st.markdown(f"### 🔗 {t['google_meet']}")
    st.warning(t["google_coming"])

    if mstatus != "confirmed":
        if st.button(t["confirm_meeting"], use_container_width=True):
            confirm_meeting_slot(mc, sel["Date"], sel["Start"], sel["End"])
            st.success(t["confirmed"])
            ics = make_ics(mtitle, sel["Date"], sel["Start"], sel["End"],
                           description=f"Confirmed via MeetAlign. Code: {mc}")
            st.download_button(t["download_ics"], data=ics,
                               file_name=f"meetalign_{mc}.ics", mime="text/calendar",
                               use_container_width=True)

    st.markdown("### ✉️ Email Confirmation")
    re = st.text_input(t["recipient_email"], value=sel.get("Participant Email", ""))
    ebody = f"""Hello,

The meeting has been confirmed.

Meeting: {mtitle}
Date: {sel['Date']}
Time: {sel['Start']} - {sel['End']}

Google Meet: Coming Soon

Best regards,
MeetAlign"""
    st.text_area("Email Preview", value=ebody, height=180)
    if st.button(t["send_email"], use_container_width=True):
        if not re:
            st.warning(t["recipient_email"])
        else:
            ok, r = send_email(re, f"Confirmed: {mtitle}", ebody)
            if ok:
                st.success(t["email_sent"])
            else:
                st.error(f"{t['email_failed']} {r}")
    card_close()

# ── AI CHATBOT ───────────────────────────────────────
elif menu == t["chatbot"]:
    st.header(t["chatbot"])
    guide(t["chat_help"])
    card_open()

    # Chat history
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Chat mode
    mode = st.radio(t["chat_mode"], [t["mode_command"], t["mode_chat"]], horizontal=True)

    # Display history
    for ch in st.session_state["chat_history"]:
        if ch["role"] == "user":
            st.markdown(f"**🧑 You:** {ch['text']}")
        else:
            st.markdown(f"**🤖 AI:** {ch['text']}")
        st.markdown("---")

    user_msg = st.text_area(t["chat_input"], height=120, placeholder=t["chat_help"])

    if st.button(t["chat_button"], use_container_width=True):
        if not user_msg:
            st.warning(t["chat_input"])
        else:
            st.session_state["chat_history"].append({"role": "user", "text": user_msg})

            if mode == t["mode_chat"]:
                # Free chat mode
                reply = ai_chatbot_response(user_msg, language=language)
                st.session_state["chat_history"].append({"role": "ai", "text": reply})
                st.markdown(f"**🤖 AI:** {reply}")

            else:
                # Create meeting from text
                parsed, error = parse_meeting_command(user_msg)
                if error:
                    st.error(error)
                    st.session_state["chat_history"].append({"role": "ai", "text": f"Error: {error}"})
                else:
                    st.subheader(t["parsed"])
                    st.json(parsed)

                    mt2 = parsed.get("meeting_title") or "MeetAlign Meeting"
                    dv = parsed.get("date", "")
                    stv = parsed.get("start_time", "")
                    etv = parsed.get("end_time", "")
                    pn = parsed.get("participant_name", "")

                    if stv and not etv:
                        try:
                            tmp = datetime.strptime(stv, "%H:%M")
                            etv = (tmp + timedelta(minutes=30)).strftime("%H:%M")
                        except Exception:
                            etv = ""

                    mc2 = create_meeting(mt2)
                    ml2 = f"{get_base_url()}?meeting={mc2}"
                    st.success(t["created"])

                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.text_input(t["meeting_code"], value=mc2, key="chat_mc")
                    with c2:
                        st.text_input(t["meeting_link"], value=ml2, key="chat_ml")

                    if dv and stv and etv:
                        add_availability(
                            mc2, "Organizer", "", t["organizer"], dv,
                            f"{stv}:00" if len(stv) == 5 else stv,
                            f"{etv}:00" if len(etv) == 5 else etv
                        )
                        st.info("Organizer availability added automatically.")

                    inv = f"""Hello {pn},

I created a meeting link for:
{mt2}

Please add your availability:
{ml2}

Meeting Code: {mc2}

Best regards"""
                    st.subheader(t["copy_invitation"])
                    st.code(inv)
                    st.session_state["chat_history"].append(
                        {"role": "ai", "text": f"Meeting created: {mt2} | Code: {mc2}"}
                    )
    card_close()

# ── MANAGE MEETINGS ──────────────────────────────────
elif menu == t["manage"]:
    st.header(t["manage"])
    guide("View all meetings. Cancel, archive or restore meetings. View history.")
    card_open()

    all_m = get_all_meetings()
    if not all_m:
        empty(t["no_meetings"])
        card_close()
        st.stop()

    st.subheader(t["all_meetings"])
    for m in all_m:
        code, title, status, created = m
        col1, col2, col3 = st.columns([3, 1, 2])
        with col1:
            st.markdown(f"**{title}** (`{code}`)")
        with col2:
            st.markdown(status_badge(status), unsafe_allow_html=True)
        with col3:
            st.caption(str(created))

    st.markdown("---")

    mc_manage = st.text_input(t["meeting_code"], key="manage_code", placeholder="AB12CD34").strip().upper()
    meeting = get_meeting(mc_manage) if mc_manage else None

    if mc_manage and not meeting:
        st.warning(t["not_found"])
    elif meeting:
        mtitle = meeting[1]
        mstatus = meeting[2]
        st.success(f"{mtitle}")
        st.markdown(f"{t['status']}: {status_badge(mstatus)}", unsafe_allow_html=True)

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            if mstatus == "active":
                if st.button(t["cancel"], use_container_width=True, key="btn_cancel"):
                    cancel_meeting(mc_manage)
                    st.warning(t["cancelled"])
                    st.rerun()

        with col_b:
            if mstatus == "active":
                if st.button(t["archive"], use_container_width=True, key="btn_archive"):
                    archive_meeting(mc_manage)
                    st.info(t["archived"])
                    st.rerun()

        with col_c:
            if mstatus in ["cancelled", "archived"]:
                if st.button(t["restore"], use_container_width=True, key="btn_restore"):
                    restore_meeting(mc_manage)
                    st.success(t["restored"])
                    st.rerun()

        st.markdown("---")
        st.subheader(t["history"])
        hist = get_meeting_history(mc_manage)
        if hist:
            for h in hist:
                action, detail, ts = h
                st.markdown(
                    f'<div class="history-row"><strong>{action}</strong> — {detail}<br>'
                    f'<small style="color:#9ca3af">{ts}</small></div>',
                    unsafe_allow_html=True
                )
        else:
            empty(t["no_history"])

    card_close()
