import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from database import (
    init_db, create_meeting, get_meeting, update_meeting_link,
    add_availability, get_availability, cancel_meeting, archive_meeting,
    restore_meeting, confirm_meeting_slot, delete_meeting_permanent,
    get_meeting_history, get_all_meetings, get_active_meetings,
    get_archived_meetings, get_confirmed_meetings
)
from ai_assistant import (
    parse_meeting_command, generate_meeting_email,
    generate_confirmation_email, ai_chatbot_response
)

init_db()
ADMIN_PASSWORD = "1234"

st.set_page_config(page_title="MeetAlign", page_icon="📅", layout="wide", initial_sidebar_state="expanded")

# ═══════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    :root{--blue:#2563eb;--indigo:#4f46e5;--green:#16a34a;--red:#dc2626;
          --amber:#d97706;--gray:#6b7280;--light:#f8fafc;--white:#ffffff}
    .stApp{background:linear-gradient(135deg,#f0f4ff 0%,#e8ecf8 50%,#f5f3ff 100%);font-family:'Inter',sans-serif}
    section[data-testid="stSidebar"]{background:linear-gradient(180deg,#fff 0%,#f8fafc 100%);border-right:1px solid #e2e8f0}
    .hero{background:linear-gradient(135deg,#fff 0%,#f0f4ff 100%);padding:36px 40px;border-radius:28px;
          border:1px solid #e2e8f0;box-shadow:0 25px 60px rgba(15,23,42,.06);margin-bottom:28px;position:relative;overflow:hidden}
    .hero::before{content:'';position:absolute;top:-50%;right:-20%;width:400px;height:400px;
                  background:radial-gradient(circle,rgba(37,99,235,.06) 0%,transparent 70%);border-radius:50%}
    .hero-title{font-size:48px;font-weight:900;color:#0f172a;margin-bottom:8px;letter-spacing:-1px;position:relative}
    .hero-sub{color:#64748b;font-size:17px;line-height:1.7;position:relative}
    .hero-steps{margin-top:16px;font-size:15px;font-weight:600;color:#334155;position:relative}
    .card{background:var(--white);padding:28px;border-radius:24px;border:1px solid #e2e8f0;
          box-shadow:0 12px 40px rgba(15,23,42,.04);margin:20px 0;transition:all .2s}
    .card:hover{box-shadow:0 16px 50px rgba(15,23,42,.06)}
    .guide{background:linear-gradient(135deg,#eff6ff 0%,#f0f4ff 100%);padding:18px 22px;border-radius:16px;
           border:1px solid #bfdbfe;color:#1e40af;margin-bottom:22px;font-size:15px;font-weight:500;line-height:1.6}
    .pill{display:inline-block;padding:6px 14px;background:#eff6ff;color:var(--blue);border-radius:999px;
          font-size:12px;font-weight:700;margin:4px 6px 4px 0;border:1px solid #bfdbfe;letter-spacing:.3px}
    .pill-green{background:#f0fdf4;color:var(--green);border-color:#bbf7d0}
    .pill-red{background:#fef2f2;color:var(--red);border-color:#fecaca}
    .pill-amber{background:#fffbeb;color:var(--amber);border-color:#fde68a}
    .pill-gray{background:#f9fafb;color:var(--gray);border-color:#e5e7eb}
    .empty{background:linear-gradient(135deg,#fff 0%,#f8fafc 100%);padding:40px;border-radius:24px;
           border:2px dashed #cbd5e1;text-align:center;color:#94a3b8;margin-top:20px}
    .empty h3{font-size:40px;margin-bottom:8px}.empty p{font-size:15px}
    .metric-row{display:flex;gap:16px;margin:20px 0}
    .metric-box{flex:1;background:linear-gradient(135deg,#fff 0%,#f8fafc 100%);padding:22px;border-radius:20px;
                border:1px solid #e2e8f0;box-shadow:0 8px 24px rgba(15,23,42,.03);text-align:center;transition:all .2s}
    .metric-box:hover{transform:translateY(-2px);box-shadow:0 12px 32px rgba(15,23,42,.06)}
    .metric-num{font-size:32px;font-weight:900;color:var(--blue)}
    .metric-lbl{font-size:13px;color:var(--gray);margin-top:4px;font-weight:600}
    .history-item{padding:12px 16px;border-left:4px solid var(--blue);margin-bottom:10px;
                  background:linear-gradient(90deg,#f0f4ff 0%,#fff 100%);border-radius:0 12px 12px 0;font-size:14px}
    .meeting-card{padding:18px 22px;border-radius:18px;border:1px solid #e2e8f0;margin-bottom:12px;
                  background:linear-gradient(135deg,#fff 0%,#fafbff 100%);transition:all .15s}
    .meeting-card:hover{border-color:#93c5fd;box-shadow:0 6px 20px rgba(37,99,235,.08);transform:translateY(-1px)}
    .meeting-card-title{font-weight:700;font-size:15px;color:#1e293b}
    .meeting-card-code{font-family:monospace;background:#f1f5f9;padding:3px 10px;border-radius:8px;
                       font-size:13px;color:#475569;font-weight:600}
    .meeting-card-date{font-size:12px;color:#94a3b8;margin-top:6px}
    .status-active{color:var(--green);font-weight:700}.status-confirmed{color:var(--blue);font-weight:700}
    .status-cancelled{color:var(--red);font-weight:700}.status-archived{color:var(--gray);font-weight:700}
    .admin-box{background:linear-gradient(135deg,#fffbeb 0%,#fef3c7 100%);border:1px solid #fcd34d;
               border-radius:18px;padding:24px;margin:16px 0;text-align:center}
    .admin-locked{background:linear-gradient(135deg,#fef2f2 0%,#fee2e2 100%);border:1px solid #fca5a5;
                  border-radius:18px;padding:28px;text-align:center;color:var(--red);margin:16px 0;font-weight:600}
    .admin-success{background:linear-gradient(135deg,#f0fdf4 0%,#dcfce7 100%);border:1px solid #86efac;
                   border-radius:14px;padding:14px 20px;color:var(--green);font-weight:700;text-align:center;margin-bottom:16px}
    .link-box{background:linear-gradient(135deg,#f0fdf4 0%,#ecfdf5 100%);border:1px solid #86efac;
              border-radius:14px;padding:14px 18px;margin:12px 0;font-size:14px;word-break:break-all}
    .link-box a{color:var(--blue);text-decoration:none;font-weight:600}
    .section-head{font-size:18px;font-weight:800;color:#1e293b;margin-bottom:14px;padding-bottom:10px;border-bottom:2px solid #e2e8f0}
    .divider{height:1px;background:linear-gradient(90deg,transparent,#e2e8f0,transparent);margin:24px 0}
    div.stButton>button{background:linear-gradient(135deg,var(--blue) 0%,var(--indigo) 100%);color:#fff;
        border:none;border-radius:14px;padding:.8rem 1.4rem;font-weight:750;
        box-shadow:0 10px 30px rgba(37,99,235,.25);transition:all .2s;font-size:14px}
    div.stButton>button:hover{background:linear-gradient(135deg,#1d4ed8 0%,#4338ca 100%);
        color:#fff;border:none;transform:translateY(-2px);box-shadow:0 14px 36px rgba(37,99,235,.3)}
    .manage-action-card{background:linear-gradient(135deg,#fff 0%,#fafbff 100%);padding:20px 24px;
        border-radius:20px;border:1px solid #e2e8f0;margin-bottom:16px}
    .manage-action-title{font-size:16px;font-weight:700;color:#1e293b;margin-bottom:12px}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# TEXT
# ═══════════════════════════════════════════════════════
TEXT = {
    "English": {
        "menu":"Workspace","create":"Create Meeting","availability":"Add Availability",
        "confirm":"Confirm & Calendar","chatbot":"AI Chatbot","manage":"Manage Meetings",
        "title":"MeetAlign",
        "subtitle":"Smart meeting scheduler for project teams, researchers and consortium partners.",
        "hero":"Create → Collect availability → Confirm → Send invite",
        "meeting_title":"Meeting Title","meeting_placeholder":"EIC Pathfinder Meeting",
        "meeting_video_link":"Zoom / Google Meet Link (optional)",
        "meeting_video_placeholder":"https://zoom.us/j/... or https://meet.google.com/...",
        "create_button":"🚀 Create Meeting","meeting_code":"Meeting Code",
        "meeting_link":"Meeting Link","copy_invitation":"📋 Copy invitation",
        "created":"✅ Meeting created!",
        "org_name":"Organizer Name","org_email":"Organizer Email",
        "org_date":"Available Date","org_start":"Start","org_end":"End",
        "org_info":"👤 Organizer Availability (auto-added)",
        "name":"Your Name","email":"Your Email","role":"Role",
        "organizer":"Organizer","participant":"Participant",
        "date":"Date","start":"Start Time","end":"End Time",
        "save":"💾 Save Availability","saved":"✅ Saved!",
        "not_found":"Meeting not found.","enter_code":"Select or enter code.",
        "enter_name":"Enter your name.","time_error":"End must be after start.",
        "blocked":"🚫 Meeting not active.","select_meeting":"Select a meeting",
        "existing_meetings":"📋 Your Meetings",
        "all_availability":"All Availability","matches":"Matching Slots",
        "no_data":"No availability yet.","no_match":"No match yet.",
        "select_slot":"Select slot","confirm_meeting":"✅ Confirm",
        "confirmed":"Confirmed!","already_confirmed":"Already confirmed",
        "download_ics":"📥 Download .ics","video_link":"🔗 Video Link",
        "no_video_link":"No video link set.","update_link":"Update","link_updated":"Updated!",
        "send_email":"📧 Send Email","recipient_email":"Recipient Email",
        "email_sent":"✅ Sent!","email_failed":"❌ Failed.",
        "generate_invite":"🤖 Generate AI Email","generated_email":"Generated Email",
        "generate_confirm_email":"🤖 Generate Confirmation Email",
        "chat_help":"Example: Plan a meeting with Moshira on 2026-05-12 at 14:00.",
        "chat_input":"Type your message...","chat_button":"Send","parsed":"AI understood:",
        "chat_mode":"Mode","mode_command":"Create Meeting","mode_chat":"Free Chat",
        "admin_password":"🔑 Password","admin_login":"Login",
        "admin_wrong":"Wrong password.","admin_locked":"🔒 Admin login required.",
        "admin_logged":"🔓 Admin access granted.",
        "cancel":"🚫 Cancel","cancel_reason":"Reason","cancelled":"Cancelled.",
        "archive":"📦 Archive","restore":"♻️ Restore","restored":"Restored.",
        "delete_permanent":"🗑️ Delete Forever","deleted":"Deleted.",
        "delete_confirm":"⚠️ Cannot be undone!",
        "active_meetings":"🟢 Active","confirmed_meetings":"🔵 Confirmed",
        "archived_meetings":"📦 Archived / Cancelled","no_meetings":"No meetings.",
        "history":"📜 History","no_history":"No history.",
        "status":"Status","entries":"Entries","match_count":"Matches","people":"People",
        "select_to_manage":"Select a meeting to manage","actions":"Actions",
        "meeting_details":"Meeting Details","generating":"Generating...",
    },
    "Türkçe": {
        "menu":"Çalışma Alanı","create":"Toplantı Oluştur","availability":"Uygunluk Ekle",
        "confirm":"Onayla & Takvim","chatbot":"AI Chatbot","manage":"Toplantı Yönetimi",
        "title":"MeetAlign",
        "subtitle":"Proje ekipleri ve araştırmacılar için akıllı toplantı planlayıcı.",
        "hero":"Oluştur → Uygunluk topla → Onayla → Davet gönder",
        "meeting_title":"Toplantı Başlığı","meeting_placeholder":"EIC Pathfinder Toplantısı",
        "meeting_video_link":"Zoom / Google Meet Linki (opsiyonel)",
        "meeting_video_placeholder":"https://zoom.us/j/... veya https://meet.google.com/...",
        "create_button":"🚀 Oluştur","meeting_code":"Meeting Code",
        "meeting_link":"Toplantı Linki","copy_invitation":"📋 Daveti kopyala",
        "created":"✅ Oluşturuldu!",
        "org_name":"Organizatör Adı","org_email":"Organizatör E-posta",
        "org_date":"Uygun Tarih","org_start":"Başlangıç","org_end":"Bitiş",
        "org_info":"👤 Organizatör Uygunluğu (otomatik eklenir)",
        "name":"Adınız","email":"E-posta","role":"Rol",
        "organizer":"Organizatör","participant":"Katılımcı",
        "date":"Tarih","start":"Başlangıç","end":"Bitiş",
        "save":"💾 Kaydet","saved":"✅ Kaydedildi!",
        "not_found":"Bulunamadı.","enter_code":"Seçin veya kod girin.",
        "enter_name":"Adınızı girin.","time_error":"Bitiş başlangıçtan sonra olmalı.",
        "blocked":"🚫 Toplantı aktif değil.","select_meeting":"Toplantı seçin",
        "existing_meetings":"📋 Toplantılar",
        "all_availability":"Tüm Uygunluklar","matches":"Ortak Saatler",
        "no_data":"Henüz uygunluk yok.","no_match":"Eşleşme yok.",
        "select_slot":"Saat seçin","confirm_meeting":"✅ Onayla",
        "confirmed":"Onaylandı!","already_confirmed":"Zaten onaylı",
        "download_ics":"📥 .ics İndir","video_link":"🔗 Video Linki",
        "no_video_link":"Video linki yok.","update_link":"Güncelle","link_updated":"Güncellendi!",
        "send_email":"📧 Gönder","recipient_email":"Alıcı E-posta",
        "email_sent":"✅ Gönderildi!","email_failed":"❌ Gönderilemedi.",
        "generate_invite":"🤖 AI Davet Oluştur","generated_email":"Oluşturulan E-posta",
        "generate_confirm_email":"🤖 AI Onay E-postası Oluştur",
        "chat_help":"Örnek: 12 Mayıs 2026 14:00'te Moshira ile toplantı planla.",
        "chat_input":"Mesajınızı yazın...","chat_button":"Gönder","parsed":"AI anladı:",
        "chat_mode":"Mod","mode_command":"Toplantı Oluştur","mode_chat":"Serbest Sohbet",
        "admin_password":"🔑 Şifre","admin_login":"Giriş",
        "admin_wrong":"Yanlış şifre.","admin_locked":"🔒 Admin girişi gerekli.",
        "admin_logged":"🔓 Erişim sağlandı.",
        "cancel":"🚫 İptal","cancel_reason":"Neden","cancelled":"İptal edildi.",
        "archive":"📦 Arşivle","restore":"♻️ Geri Al","restored":"Geri alındı.",
        "delete_permanent":"🗑️ Kalıcı Sil","deleted":"Silindi.",
        "delete_confirm":"⚠️ Geri alınamaz!",
        "active_meetings":"🟢 Aktif","confirmed_meetings":"🔵 Onaylı",
        "archived_meetings":"📦 Arşiv / İptal","no_meetings":"Toplantı yok.",
        "history":"📜 Geçmiş","no_history":"Geçmiş yok.",
        "status":"Durum","entries":"Kayıt","match_count":"Eşleşme","people":"Kişi",
        "select_to_manage":"Yönetilecek toplantıyı seçin","actions":"İşlemler",
        "meeting_details":"Toplantı Detayları","generating":"Oluşturuluyor...",
    }
}

# ═══════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════
def base_url():
    try: return st.context.url.split("?")[0]
    except: return "https://your-app.streamlit.app"

def q_code():
    try: return st.query_params.get("meeting","")
    except: return ""

def card_open():
    st.markdown('<div class="card">', unsafe_allow_html=True)

def card_close():
    st.markdown('</div>', unsafe_allow_html=True)

def guide(txt):
    st.markdown(f'<div class="guide">{txt}</div>', unsafe_allow_html=True)

def empty(msg):
    st.markdown(f'<div class="empty"><h3>📭</h3><p>{msg}</p></div>', unsafe_allow_html=True)

def divider():
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

def sbadge(s):
    return f'<span class="status-{s}">{s.upper()}</span>'

def pill_html(text, cls=""):
    c = f" {cls}" if cls else ""
    return f'<span class="pill{c}">{text}</span>'

def metrics_html(items):
    b = "".join(f'<div class="metric-box"><div class="metric-num">{n}</div><div class="metric-lbl">{l}</div></div>' for n,l in items)
    st.markdown(f'<div class="metric-row">{b}</div>', unsafe_allow_html=True)

def mchtml(code, title, status, dt=""):
    return f"""<div class="meeting-card"><div style="display:flex;justify-content:space-between;align-items:center">
        <div><span class="meeting-card-title">{title}</span>&nbsp;&nbsp;
        <span class="meeting-card-code">{code}</span>&nbsp;&nbsp;{sbadge(status)}</div>
        <div class="meeting-card-date">{dt}</div></div></div>"""

def get_df(mc):
    rows = get_availability(mc)
    if not rows: return pd.DataFrame()
    return pd.DataFrame(rows, columns=["Name","Email","Role","Date","Start Time","End Time"])

def calc_matches(df, ol, pl):
    orgs = df[df["Role"]==ol]; parts = df[df["Role"]==pl]; out=[]
    for _,o in orgs.iterrows():
        for _,p in parts.iterrows():
            if o["Date"]==p["Date"]:
                s=max(o["Start Time"],p["Start Time"]); e=min(o["End Time"],p["End Time"])
                if s<e: out.append({"Date":o["Date"],"Start":s,"End":e,"Organizer":o["Name"],
                                    "Participant":p["Name"],"Participant Email":p["Email"]})
    return out

def make_ics(title,ds,ss,es,desc="",vl=""):
    ss,es=str(ss),str(es)
    if len(ss)==5:ss+=":00"
    if len(es)==5:es+=":00"
    s=datetime.strptime(f"{ds} {ss}","%Y-%m-%d %H:%M:%S")
    e=datetime.strptime(f"{ds} {es}","%Y-%m-%d %H:%M:%S")
    st_=datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    fd=desc+(f"\\nVideo: {vl}" if vl else "")
    return f"""BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//MeetAlign//EN\nBEGIN:VEVENT\nUID:{st_}@meetalign\nDTSTAMP:{st_}\nDTSTART:{s.strftime("%Y%m%dT%H%M%S")}\nDTEND:{e.strftime("%Y%m%dT%H%M%S")}\nSUMMARY:{title}\nDESCRIPTION:{fd}\nLOCATION:{vl}\nEND:VEVENT\nEND:VCALENDAR"""

def send_resend(to,subj,body):
    ak=st.secrets.get("RESEND_API_KEY",""); se=st.secrets.get("SENDER_EMAIL","")
    if not ak or not se: return False,"RESEND keys missing."
    try:
        r=requests.post("https://api.resend.com/emails",
            json={"from":se,"to":[to],"subject":subj,"html":body.replace("\n","<br>")},
            headers={"Authorization":f"Bearer {ak}","Content-Type":"application/json"},timeout=30)
        return (r.status_code in [200,201,202]),r.text
    except Exception as ex: return False,str(ex)

def is_blocked(m):
    if not m: return True
    return m[2] in ("cancelled","archived")

def check_admin():
    return st.session_state.get("admin_auth",False)

def all_meetings_for_select():
    a = get_active_meetings(); c = get_confirmed_meetings()
    return a + c

def all_meetings_for_manage():
    return get_all_meetings()

# ═══════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════
lang = st.sidebar.selectbox("🌐 Language / Dil",["English","Türkçe"])
t = TEXT[lang]; qc = q_code()
st.sidebar.markdown("---")
st.sidebar.markdown("### 📅 MeetAlign")
st.sidebar.caption(t["subtitle"])
st.sidebar.markdown("---")
menu = st.sidebar.radio(t["menu"],
    [t["create"],t["availability"],t["confirm"],t["chatbot"],t["manage"]],
    index=1 if qc else 0)
if check_admin():
    st.sidebar.markdown("---")
    if st.sidebar.button("🔒 Logout Admin",key="sb_logout"):
        st.session_state["admin_auth"]=False; st.rerun()

# ═══════════════════════════════════════════════════════
# HERO
# ═══════════════════════════════════════════════════════
st.markdown(f"""<div class="hero">
    {pill_html("📋 Availability")} {pill_html("📅 Calendar")} {pill_html("🤖 AI")}
    {pill_html("🎥 Zoom/Meet","pill-green")} {pill_html("⚙️ Admin","pill-gray")}
    <div class="hero-title">📅 {t["title"]}</div>
    <div class="hero-sub">{t["subtitle"]}</div>
    <div class="hero-steps">{t["hero"]}</div>
</div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# 1. CREATE MEETING
# ═══════════════════════════════════════════════════════
if menu == t["create"]:
    st.header(f"🆕 {t['create']}")
    guide("1️⃣ Title & video link → 2️⃣ Your availability → 3️⃣ Create → 4️⃣ Share")
    card_open()
    st.markdown('<div class="section-head">📝 Meeting Details</div>', unsafe_allow_html=True)
    mt = st.text_input(t["meeting_title"], placeholder=t["meeting_placeholder"])
    vl = st.text_input(t["meeting_video_link"], placeholder=t["meeting_video_placeholder"])
    divider()
    st.markdown(f'<div class="section-head">{t["org_info"]}</div>', unsafe_allow_html=True)
    oc1,oc2 = st.columns(2)
    with oc1:
        org_name = st.text_input(t["org_name"], placeholder="John Doe")
        org_email = st.text_input(t["org_email"], placeholder="john@example.com")
    with oc2:
        org_date = st.date_input(t["org_date"])
        osc1,osc2 = st.columns(2)
        with osc1: org_start = st.time_input(t["org_start"])
        with osc2: org_end = st.time_input(t["org_end"])
    st.markdown("")
    if st.button(t["create_button"], use_container_width=True):
        if not mt: st.warning(t["meeting_title"])
        elif not org_name: st.warning(t["enter_name"])
        elif org_start >= org_end: st.warning(t["time_error"])
        else:
            mc = create_meeting(mt, vl)
            ml = f"{base_url()}?meeting={mc}"
            add_availability(mc,org_name,org_email,t["organizer"],org_date,org_start,org_end)
            st.success(t["created"])
            c1,c2 = st.columns([1,2])
            with c1: st.text_input(t["meeting_code"],value=mc,disabled=True,key="cr_mc")
            with c2: st.text_input(t["meeting_link"],value=ml,disabled=True,key="cr_ml")
            if vl: st.markdown(f'<div class="link-box">🎥 <a href="{vl}" target="_blank">{vl}</a></div>', unsafe_allow_html=True)
            st.info(f"👤 {org_name} — {org_date} | {org_start}-{org_end}")
            divider()
            st.subheader(t["copy_invitation"])
            vline = f"\nVideo: {vl}" if vl else ""
            st.code(f"""Hello,\n\nMeeting: {mt}\nLink: {ml}\nCode: {mc}{vline}\n\nOrganizer: {org_name}\nAvailable: {org_date} | {org_start}-{org_end}\n\nBest regards""")
    card_close()


# ═══════════════════════════════════════════════════════
# 2. ADD AVAILABILITY
# ═══════════════════════════════════════════════════════
elif menu == t["availability"]:
    st.header(f"📝 {t['availability']}")
    guide("1️⃣ Select meeting from list → 2️⃣ Fill details → 3️⃣ Save")

    avail_list = all_meetings_for_select()

    card_open()
    st.markdown(f'<div class="section-head">{t["existing_meetings"]}</div>', unsafe_allow_html=True)

    if avail_list:
        for m in avail_list:
            st.markdown(mchtml(m[0],m[1],m[2],m[3]), unsafe_allow_html=True)
    else:
        empty(t["no_meetings"])

    # Dropdown ile seçim - seçince direkt o toplantıya geçer
    options_codes = [m[0] for m in avail_list] if avail_list else []
    options_labels = {m[0]: f"📋 {m[0]} — {m[1]}" for m in avail_list} if avail_list else {}

    # Query code varsa onu default yap
    default_idx = 0
    if qc and qc.upper() in [c.upper() for c in options_codes]:
        for i,c in enumerate(options_codes):
            if c.upper() == qc.upper():
                default_idx = i + 1; break

    sel_options = [""] + options_codes
    sel_meeting = st.selectbox(
        t["select_meeting"], sel_options,
        index=default_idx,
        format_func=lambda x: options_labels.get(x, f"— {t['enter_code']} —") if x else f"— {t['enter_code']} —",
        key="avail_sel"
    )

    # Seçilen meeting kodu - artık tekrar input yok
    mc = sel_meeting.strip().upper() if sel_meeting else ""

    # Eğer listede yoksa manuel giriş
    if not mc:
        mc = st.text_input(t["meeting_code"], placeholder="AB12CD34", key="avail_manual").strip().upper()

    card_close()

    meeting = get_meeting(mc) if mc else None

    if mc and not meeting:
        st.warning(t["not_found"])
        st.stop()

    if meeting:
        if is_blocked(meeting):
            st.error(t["blocked"])
            st.stop()

        card_open()
        st.success(f"📋 {meeting[1]}")
        st.markdown(f"{t['status']}: {sbadge(meeting[2])}", unsafe_allow_html=True)
        if meeting[3]:
            st.markdown(f'<div class="link-box">🎥 <a href="{meeting[3]}" target="_blank">{meeting[3]}</a></div>', unsafe_allow_html=True)

        # Mevcut uygunluklar
        edf = get_df(mc)
        if not edf.empty:
            divider()
            st.markdown(f'<div class="section-head">📊 {t["all_availability"]}</div>', unsafe_allow_html=True)
            metrics_html([(len(edf),t["entries"]),(edf["Email"].nunique(),t["people"])])
            st.dataframe(edf, use_container_width=True, hide_index=True)

        divider()
        st.markdown('<div class="section-head">➕ Add Your Availability</div>', unsafe_allow_html=True)

        c1,c2 = st.columns(2)
        with c1:
            name = st.text_input(t["name"])
            email = st.text_input(t["email"])
        with c2:
            role = st.selectbox(t["role"],[t["organizer"],t["participant"]])
            date = st.date_input(t["date"])
            sc1,sc2 = st.columns(2)
            with sc1: start_time = st.time_input(t["start"])
            with sc2: end_time = st.time_input(t["end"])

        st.markdown("")
        if st.button(t["save"], use_container_width=True):
            if not name: st.warning(t["enter_name"])
            elif start_time >= end_time: st.warning(t["time_error"])
            else:
                add_availability(mc,name,email,role,date,start_time,end_time)
                st.success(t["saved"])
                st.rerun()
        card_close()
    elif not mc:
        st.info(t["enter_code"])


# ═══════════════════════════════════════════════════════
# 3. CONFIRM & CALENDAR
# ═══════════════════════════════════════════════════════
elif menu == t["confirm"]:
    st.header(f"✅ {t['confirm']}")
    guide("1️⃣ Select meeting → 2️⃣ View matches → 3️⃣ Confirm → 4️⃣ .ics / Email")

    avail_list = all_meetings_for_select()
    card_open()

    options_codes = [m[0] for m in avail_list] if avail_list else []
    options_labels = {m[0]: f"📋 {m[0]} — {m[1]}" for m in avail_list} if avail_list else {}
    default_idx = 0
    if qc and qc.upper() in [c.upper() for c in options_codes]:
        for i,c in enumerate(options_codes):
            if c.upper()==qc.upper(): default_idx=i+1; break

    sel = st.selectbox(t["select_meeting"],[""] + options_codes, index=default_idx,
        format_func=lambda x: options_labels.get(x,f"— {t['enter_code']} —") if x else f"— {t['enter_code']} —",
        key="conf_sel")
    mc = sel.strip().upper() if sel else ""
    if not mc:
        mc = st.text_input(t["meeting_code"],placeholder="AB12CD34",key="conf_manual").strip().upper()

    card_close()

    meeting = get_meeting(mc) if mc else None
    if not mc: st.info(t["enter_code"]); st.stop()
    if not meeting: st.warning(t["not_found"]); st.stop()
    if is_blocked(meeting): st.error(t["blocked"]); st.stop()

    mtitle,mstatus,vlink = meeting[1],meeting[2],meeting[3]

    card_open()
    st.success(f"📋 {mtitle}")
    st.markdown(f"{t['status']}: {sbadge(mstatus)}", unsafe_allow_html=True)

    # Video link
    st.markdown(f"### {t['video_link']}")
    if vlink:
        st.markdown(f'<div class="link-box">🎥 <a href="{vlink}" target="_blank">{vlink}</a></div>', unsafe_allow_html=True)
    else:
        st.info(t["no_video_link"])
    nvl = st.text_input(t["meeting_video_link"],value=vlink or "",key="upd_vl",placeholder=t["meeting_video_placeholder"])
    if st.button(t["update_link"],key="btn_upd"):
        update_meeting_link(mc,nvl); st.success(t["link_updated"]); st.rerun()

    if mstatus == "confirmed":
        st.info(f"{t['already_confirmed']}: {meeting[4]} | {meeting[5]}-{meeting[6]}")
        ics = make_ics(mtitle,meeting[4],meeting[5],meeting[6],f"MeetAlign: {mc}",vlink)
        st.download_button(t["download_ics"],data=ics,file_name=f"meetalign_{mc}.ics",
                           mime="text/calendar",use_container_width=True)

    df = get_df(mc)
    if df.empty: empty(t["no_data"]); card_close(); st.stop()

    divider()
    st.subheader(t["all_availability"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    matches = calc_matches(df,t["organizer"],t["participant"])
    st.subheader(t["matches"])
    if not matches: empty(t["no_match"]); card_close(); st.stop()

    metrics_html([(len(df),t["entries"]),(len(matches),t["match_count"]),(df["Email"].nunique(),t["people"])])
    mdf = pd.DataFrame(matches)
    st.dataframe(mdf, use_container_width=True, hide_index=True)

    # AI Invitation Email
    divider()
    st.markdown(f'<div class="section-head">{t["generate_invite"]}</div>', unsafe_allow_html=True)
    if st.button(t["generate_invite"], key="gen_inv"):
        with st.spinner(t.get("generating","Generating...")):
            try:
                ie = generate_meeting_email(mtitle, matches, language=lang, meeting_link=vlink or "")
                st.session_state["inv_email"] = ie
            except Exception as e:
                st.error(f"Error: {e}")

    if "inv_email" in st.session_state and st.session_state["inv_email"]:
        st.subheader(t["generated_email"])
        st.text_area("",value=st.session_state["inv_email"],height=280,key="inv_ta")

    # Slot seçimi ve onay
    divider()
    si = st.selectbox(t["select_slot"],range(len(matches)),
        format_func=lambda i: f"📅 {matches[i]['Date']} | ⏰ {matches[i]['Start']}-{matches[i]['End']}")
    sel_m = matches[si]
    st.markdown(f"### ✅ **{sel_m['Date']}** | **{sel_m['Start']}** – **{sel_m['End']}**")

    if mstatus != "confirmed":
        if st.button(t["confirm_meeting"], use_container_width=True):
            confirm_meeting_slot(mc,sel_m["Date"],sel_m["Start"],sel_m["End"])
            st.success(t["confirmed"])
            ics = make_ics(mtitle,sel_m["Date"],sel_m["Start"],sel_m["End"],f"MeetAlign: {mc}",vlink)
            st.download_button(t["download_ics"],data=ics,file_name=f"meetalign_{mc}.ics",
                               mime="text/calendar",use_container_width=True)

    # AI Confirmation Email
    divider()
    st.markdown(f'<div class="section-head">✉️ {t["generate_confirm_email"]}</div>', unsafe_allow_html=True)
    re = st.text_input(t["recipient_email"],value=sel_m.get("Participant Email",""),key="conf_re")

    if st.button(t["generate_confirm_email"], key="gen_conf"):
        with st.spinner(t.get("generating","Generating...")):
            try:
                ab = generate_confirmation_email(mtitle,sel_m["Date"],sel_m["Start"],sel_m["End"],
                                                 language=lang,meeting_link=vlink or "")
                st.session_state["conf_body"] = ab
            except Exception as e:
                st.error(f"Error: {e}")

    ebody = st.text_area("Email Preview",
        value=st.session_state.get("conf_body",f"Meeting: {mtitle}\nDate: {sel_m['Date']}\nTime: {sel_m['Start']}-{sel_m['End']}\n\nClick 'Generate' above for AI email."),
        height=220,key="conf_ta")

    if st.button(t["send_email"], use_container_width=True, key="btn_send"):
        if not re: st.warning(t["recipient_email"])
        else:
            ok,msg = send_resend(re,f"Confirmed: {mtitle}",ebody)
            if ok: st.success(t["email_sent"])
            else: st.error(f"{t['email_failed']} {msg}")
    card_close()


# ═══════════════════════════════════════════════════════
# 4. AI CHATBOT
# ═══════════════════════════════════════════════════════
elif menu == t["chatbot"]:
    st.header(f"🤖 {t['chatbot']}")
    guide(t["chat_help"])
    card_open()
    if "chat_history" not in st.session_state: st.session_state["chat_history"]=[]
    mode = st.radio(t["chat_mode"],[t["mode_command"],t["mode_chat"]],horizontal=True)

    for ch in st.session_state["chat_history"]:
        icon = "🧑" if ch["role"]=="user" else "🤖"
        st.markdown(f"**{icon}** {ch['text']}"); st.markdown("---")

    um = st.text_area(t["chat_input"],height=120,placeholder=t["chat_help"])
    if st.button(t["chat_button"],use_container_width=True):
        if not um: st.warning(t["chat_input"])
        else:
            st.session_state["chat_history"].append({"role":"user","text":um})
            if mode==t["mode_chat"]:
                with st.spinner("..."):
                    reply = ai_chatbot_response(um,language=lang)
                st.session_state["chat_history"].append({"role":"ai","text":reply}); st.rerun()
            else:
                with st.spinner("..."):
                    parsed,err = parse_meeting_command(um)
                if err:
                    st.error(err); st.session_state["chat_history"].append({"role":"ai","text":f"Error: {err}"})
                else:
                    st.subheader(t["parsed"]); st.json(parsed)
                    mt2 = parsed.get("meeting_title") or "MeetAlign Meeting"
                    dv,stv,etv = parsed.get("date",""),parsed.get("start_time",""),parsed.get("end_time","")
                    pn = parsed.get("participant_name","")
                    if stv and not etv:
                        try: etv=(datetime.strptime(stv,"%H:%M")+timedelta(minutes=30)).strftime("%H:%M")
                        except: etv=""
                    mc2 = create_meeting(mt2)
                    ml2 = f"{base_url()}?meeting={mc2}"
                    st.success(t["created"])
                    c1,c2=st.columns([1,2])
                    with c1: st.text_input(t["meeting_code"],value=mc2,key="ch_mc",disabled=True)
                    with c2: st.text_input(t["meeting_link"],value=ml2,key="ch_ml",disabled=True)
                    if dv and stv and etv:
                        add_availability(mc2,"Organizer","",t["organizer"],dv,
                            f"{stv}:00" if len(stv)==5 else stv,f"{etv}:00" if len(etv)==5 else etv)
                        st.info("✅ Organizer availability added.")
                    st.subheader(t["copy_invitation"])
                    st.code(f"Hello {pn},\n\nMeeting: {mt2}\nLink: {ml2}\nCode: {mc2}\n\nBest regards")
                    st.session_state["chat_history"].append({"role":"ai","text":f"Created: {mt2} | {mc2}"})
    card_close()


# ═══════════════════════════════════════════════════════
# 5. MANAGE MEETINGS (ADMIN)
# ═══════════════════════════════════════════════════════
elif menu == t["manage"]:
    st.header(f"⚙️ {t['manage']}")

    if not check_admin():
        card_open()
        st.markdown('<div class="admin-box">🔐 <strong>Admin Authentication</strong></div>', unsafe_allow_html=True)
        apw = st.text_input(t["admin_password"],type="password",key="apw")
        if st.button(t["admin_login"],use_container_width=True,key="btn_adm"):
            if apw==ADMIN_PASSWORD: st.session_state["admin_auth"]=True; st.rerun()
            else: st.error(t["admin_wrong"])
        card_close()
        st.markdown(f'<div class="admin-locked">{t["admin_locked"]}</div>', unsafe_allow_html=True)
        st.stop()

    st.markdown(f'<div class="admin-success">🔓 {t["admin_logged"]}</div>', unsafe_allow_html=True)
    guide("Select any meeting below to manage. Cancel, archive, restore or permanently delete.")

    all_m = all_meetings_for_manage()

    if not all_m:
        empty(t["no_meetings"]); st.stop()

    # Toplantı listesi - dropdown ile seç
    card_open()
    st.markdown(f'<div class="section-head">{t["select_to_manage"]}</div>', unsafe_allow_html=True)

    # Tüm toplantıları kartlarla göster
    tabs = st.tabs([t["active_meetings"], t["confirmed_meetings"], t["archived_meetings"]])

    with tabs[0]:
        actives = get_active_meetings()
        if actives:
            for m in actives: st.markdown(mchtml(m[0],m[1],m[2],m[3]), unsafe_allow_html=True)
        else: empty(t["no_meetings"])

    with tabs[1]:
        confirmed = get_confirmed_meetings()
        if confirmed:
            for m in confirmed: st.markdown(mchtml(m[0],m[1],m[2],m[3]), unsafe_allow_html=True)
        else: empty(t["no_meetings"])

    with tabs[2]:
        archived = get_archived_meetings()
        if archived:
            for a in archived:
                reason = f" — <em>{a[4]}</em>" if a[4] else ""
                st.markdown(f"""<div class="meeting-card" style="border-color:#fecaca">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                    <div><span class="meeting-card-title">{a[1]}</span>&nbsp;
                    <span class="meeting-card-code">{a[0]}</span>{reason}</div>
                    <div class="meeting-card-date">{a[3]}</div></div></div>""", unsafe_allow_html=True)
        else: empty(t["no_meetings"])

    # Dropdown ile toplantı seç
    divider()
    labels = {m[0]: f"{m[1]} ({m[0]}) [{m[2]}]" for m in all_m}
    sel_code = st.selectbox(
        t["select_to_manage"],
        [m[0] for m in all_m],
        format_func=lambda x: labels.get(x,x),
        key="manage_sel"
    )
    card_close()

    # Seçilen toplantının detayları ve işlemleri
    meeting = get_meeting(sel_code) if sel_code else None

    if meeting:
        card_open()
        st.markdown(f'<div class="section-head">📋 {t["meeting_details"]}</div>', unsafe_allow_html=True)
        st.markdown(f"### {meeting[1]}")
        st.markdown(f"**Code:** `{sel_code}` &nbsp;&nbsp; {t['status']}: {sbadge(meeting[2])}", unsafe_allow_html=True)

        if meeting[3]:
            st.markdown(f'<div class="link-box">🎥 <a href="{meeting[3]}" target="_blank">{meeting[3]}</a></div>', unsafe_allow_html=True)

        if meeting[2]=="confirmed" and meeting[4]:
            st.info(f"📅 Confirmed: {meeting[4]} | {meeting[5]}-{meeting[6]}")

        # Uygunluklar
        edf = get_df(sel_code)
        if not edf.empty:
            divider()
            st.markdown(f'<div class="section-head">📊 {t["all_availability"]}</div>', unsafe_allow_html=True)
            st.dataframe(edf, use_container_width=True, hide_index=True)

        # İşlemler
        divider()
        st.markdown(f'<div class="section-head">🔧 {t["actions"]}</div>', unsafe_allow_html=True)

        mstatus = meeting[2]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if mstatus in ("active","confirmed"):
                reason = st.text_input(t["cancel_reason"],key="mg_reason",placeholder="Optional reason")
                if st.button(t["cancel"],use_container_width=True,key="mg_cancel"):
                    cancel_meeting(sel_code,reason); st.warning(t["cancelled"]); st.rerun()

        with col2:
            if mstatus in ("active","confirmed"):
                st.markdown("")
                if st.button(t["archive"],use_container_width=True,key="mg_archive"):
                    archive_meeting(sel_code); st.info("Archived."); st.rerun()

        with col3:
            if mstatus in ("cancelled","archived"):
                st.markdown("")
                if st.button(t["restore"],use_container_width=True,key="mg_restore"):
                    restore_meeting(sel_code); st.success(t["restored"]); st.rerun()

        with col4:
            if mstatus in ("cancelled","archived"):
                st.caption(t["delete_confirm"])
                if st.button(t["delete_permanent"],use_container_width=True,key="mg_del"):
                    delete_meeting_permanent(sel_code); st.error(t["deleted"]); st.rerun()

        # Video link güncelle
        divider()
        st.markdown('<div class="section-head">🔗 Update Video Link</div>', unsafe_allow_html=True)
        new_vl = st.text_input(t["meeting_video_link"],value=meeting[3] or "",key="mg_vl")
        if st.button(t["update_link"],key="mg_upd"):
            update_meeting_link(sel_code,new_vl); st.success(t["link_updated"]); st.rerun()

        # Geçmiş
        divider()
        st.markdown(f'<div class="section-head">{t["history"]}</div>', unsafe_allow_html=True)
        hist = get_meeting_history(sel_code)
        if hist:
            for h in hist:
                st.markdown(f'<div class="history-item"><strong>{h[0]}</strong> — {h[1]}<br>'
                            f'<small style="color:#94a3b8">{h[2]}</small></div>', unsafe_allow_html=True)
        else: empty(t["no_history"])
        card_close()
