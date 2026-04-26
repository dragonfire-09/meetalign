import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from database import (
    init_db,
    create_meeting,
    get_meeting,
    update_meeting_link,
    add_availability,
    get_availability,
    cancel_meeting,
    archive_meeting,
    restore_meeting,
    confirm_meeting_slot,
    delete_meeting_permanent,
    get_meeting_history,
    get_all_meetings,
    get_active_meetings,
    get_archived_meetings,
    get_confirmed_meetings
)
from ai_assistant import (
    parse_meeting_command,
    generate_meeting_email,
    generate_confirmation_email,
    ai_chatbot_response
)

init_db()

st.set_page_config(page_title="MeetAlign", page_icon="📅", layout="wide", initial_sidebar_state="expanded")

# ── CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
    :root{--blue:#2563eb;--indigo:#4f46e5;--green:#16a34a;--red:#dc2626;--gray:#6b7280;--light:#f8fafc}
    .stApp{background:linear-gradient(180deg,#f8fafc 0%,#eef2ff 100%)}
    section[data-testid="stSidebar"]{background:#fff;border-right:1px solid #e5e7eb}
    .hero{background:#fff;padding:32px;border-radius:28px;border:1px solid #e5e7eb;
          box-shadow:0 20px 50px rgba(15,23,42,.07);margin-bottom:26px}
    .hero-title{font-size:44px;font-weight:900;color:#111827;margin-bottom:8px;letter-spacing:-0.5px}
    .hero-sub{color:#6b7280;font-size:17px;line-height:1.6}
    .card{background:#fff;padding:26px;border-radius:24px;border:1px solid #e5e7eb;
          box-shadow:0 12px 35px rgba(15,23,42,.05);margin:18px 0}
    .guide{background:var(--light);padding:16px 20px;border-radius:16px;border:1px solid #e5e7eb;
           color:#475569;margin-bottom:20px;font-size:15px;line-height:1.6}
    .pill{display:inline-block;padding:6px 14px;background:#eff6ff;color:var(--blue);
          border-radius:999px;font-size:12px;font-weight:700;margin:4px 6px 4px 0;border:1px solid #bfdbfe}
    .pill-green{background:#f0fdf4;color:var(--green);border-color:#bbf7d0}
    .pill-red{background:#fef2f2;color:var(--red);border-color:#fecaca}
    .pill-gray{background:#f9fafb;color:var(--gray);border-color:#e5e7eb}
    .empty{background:#fff;padding:30px;border-radius:22px;border:1px dashed #cbd5e1;
           text-align:center;color:#64748b;margin-top:18px}
    .metric-row{display:flex;gap:14px;margin:16px 0}
    .metric-box{flex:1;background:#fff;padding:18px;border-radius:18px;border:1px solid #e5e7eb;
                box-shadow:0 6px 20px rgba(15,23,42,.04);text-align:center}
    .metric-num{font-size:30px;font-weight:800;color:var(--blue)}
    .metric-lbl{font-size:13px;color:var(--gray);margin-top:4px}
    .history-item{padding:10px 14px;border-left:3px solid var(--blue);margin-bottom:8px;
                  background:var(--light);border-radius:0 10px 10px 0;font-size:14px}
    .meeting-row{padding:14px 18px;border-radius:14px;border:1px solid #e5e7eb;margin-bottom:10px;
                 background:#fff;display:flex;justify-content:space-between;align-items:center}
    .status-active{color:var(--green);font-weight:700}
    .status-confirmed{color:var(--blue);font-weight:700}
    .status-cancelled{color:var(--red);font-weight:700}
    .status-archived{color:var(--gray);font-weight:700}
    div.stButton>button{background:linear-gradient(90deg,var(--blue),var(--indigo));color:#fff;
        border:none;border-radius:14px;padding:.75rem 1.25rem;font-weight:750;
        box-shadow:0 10px 24px rgba(37,99,235,.28);transition:all .2s}
    div.stButton>button:hover{background:linear-gradient(90deg,#1d4ed8,#4338ca);
        color:#fff;border:none;transform:translateY(-1px)}
    .link-box{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:12px 16px;
              margin:10px 0;font-size:14px;word-break:break-all}
    .link-box a{color:var(--blue);text-decoration:none;font-weight:600}
</style>
""", unsafe_allow_html=True)

# ── TEXT ─────────────────────────────────────────────────────────
TEXT = {
    "English": {
        "menu":"Workspace", "create":"Create Meeting", "availability":"Add Availability",
        "confirm":"Confirm & Calendar", "chatbot":"AI Chatbot", "manage":"Manage Meetings",
        "title":"MeetAlign",
        "subtitle":"Smart meeting scheduler for project teams, researchers and consortium partners.",
        "hero":"Create a link → collect availability → confirm a slot → send calendar invite.",
        "meeting_title":"Meeting Title", "meeting_placeholder":"EIC Pathfinder Collaboration Meeting",
        "meeting_video_link":"Zoom / Google Meet Link (optional)",
        "meeting_video_placeholder":"https://zoom.us/j/... or https://meet.google.com/...",
        "create_button":"Create Meeting Link", "meeting_code":"Meeting Code",
        "meeting_link":"Meeting Link", "copy_invitation":"Copy invitation message",
        "created":"Meeting created successfully.",
        "name":"Your Name", "email":"Your Email", "role":"Role",
        "organizer":"Organizer", "participant":"Participant",
        "date":"Date", "start":"Start Time", "end":"End Time",
        "save":"Save Availability", "saved":"Availability saved.",
        "not_found":"Meeting not found.", "enter_code":"Please enter Meeting Code.",
        "enter_name":"Please enter your name.",
        "time_error":"End time must be later than start time.",
        "blocked":"This meeting is not active. Availability cannot be added.",
        "all_availability":"All Availability", "matches":"Matching Slots",
        "no_data":"No availability added yet.", "no_match":"No matching slot found.",
        "select_slot":"Select slot to confirm", "confirm_meeting":"Confirm Meeting",
        "confirmed":"Meeting confirmed.", "already_confirmed":"Already confirmed",
        "download_ics":"Download .ics Calendar Invite",
        "video_link":"Video Meeting Link", "no_video_link":"No video link set. Organizer can add it in Create Meeting.",
        "update_link":"Update Video Link", "link_updated":"Video link updated.",
        "send_email":"Send AI Confirmation Email", "recipient_email":"Recipient Email",
        "email_sent":"Email sent.", "email_failed":"Email failed.",
        "generate_invite":"Generate AI Invitation Email", "generated_email":"Generated Email",
        "chat_help":"Example: Plan a meeting with Moshira on 2026-05-12 at 14:00 for EIC Pathfinder.",
        "chat_input":"Write your request or ask a question",
        "chat_button":"Send", "parsed":"AI understood:",
        "chat_mode":"Mode", "mode_command":"Create Meeting", "mode_chat":"Free Chat",
        "cancel":"Cancel Meeting", "cancel_reason":"Reason",
        "cancelled":"Meeting cancelled.", "archive":"Archive",
        "restore":"Restore", "restored":"Restored.",
        "delete_permanent":"Delete Permanently", "deleted":"Permanently deleted.",
        "delete_confirm":"Are you sure? This cannot be undone.",
        "active_meetings":"Active Meetings", "confirmed_meetings":"Confirmed Meetings",
        "archived_meetings":"Archived / Cancelled", "no_meetings":"No meetings.",
        "history":"History", "no_history":"No history.",
        "status":"Status", "entries":"Entries", "match_count":"Matches", "people":"People",
    },
    "Türkçe": {
        "menu":"Çalışma Alanı", "create":"Toplantı Oluştur", "availability":"Uygunluk Ekle",
        "confirm":"Onayla & Takvim", "chatbot":"AI Chatbot", "manage":"Toplantı Yönetimi",
        "title":"MeetAlign",
        "subtitle":"Proje ekipleri, araştırmacılar ve konsorsiyum ortakları için akıllı toplantı planlayıcı.",
        "hero":"Link oluştur → uygunluk topla → ortak saati onayla → takvim daveti gönder.",
        "meeting_title":"Toplantı Başlığı", "meeting_placeholder":"EIC Pathfinder İş Birliği Toplantısı",
        "meeting_video_link":"Zoom / Google Meet Linki (opsiyonel)",
        "meeting_video_placeholder":"https://zoom.us/j/... veya https://meet.google.com/...",
        "create_button":"Toplantı Linki Oluştur", "meeting_code":"Meeting Code",
        "meeting_link":"Toplantı Linki", "copy_invitation":"Davet mesajını kopyala",
        "created":"Toplantı oluşturuldu.",
        "name":"Adınız", "email":"E-posta", "role":"Rol",
        "organizer":"Organizatör", "participant":"Katılımcı",
        "date":"Tarih", "start":"Başlangıç", "end":"Bitiş",
        "save":"Kaydet", "saved":"Kaydedildi.",
        "not_found":"Toplantı bulunamadı.", "enter_code":"Meeting Code girin.",
        "enter_name":"Adınızı girin.",
        "time_error":"Bitiş saati başlangıçtan sonra olmalı.",
        "blocked":"Bu toplantı aktif değil. Uygunluk eklenemez.",
        "all_availability":"Tüm Uygunluklar", "matches":"Ortak Saatler",
        "no_data":"Henüz uygunluk yok.", "no_match":"Ortak saat bulunamadı.",
        "select_slot":"Onaylanacak saati seçin", "confirm_meeting":"Onayla",
        "confirmed":"Onaylandı.", "already_confirmed":"Zaten onaylanmış",
        "download_ics":".ics İndir",
        "video_link":"Video Toplantı Linki", "no_video_link":"Video linki yok. Organizatör ekleyebilir.",
        "update_link":"Linki Güncelle", "link_updated":"Link güncellendi.",
        "send_email":"AI Onay E-postası Gönder", "recipient_email":"Alıcı E-posta",
        "email_sent":"Gönderildi.", "email_failed":"Gönderilemedi.",
        "generate_invite":"AI Davet E-postası Oluştur", "generated_email":"Oluşturulan E-posta",
        "chat_help":"Örnek: 12 Mayıs 2026 saat 14:00'te Moshira ile toplantı planla.",
        "chat_input":"İsteğinizi yazın veya soru sorun",
        "chat_button":"Gönder", "parsed":"AI anladı:",
        "chat_mode":"Mod", "mode_command":"Toplantı Oluştur", "mode_chat":"Serbest Sohbet",
        "cancel":"İptal Et", "cancel_reason":"Neden",
        "cancelled":"İptal edildi.", "archive":"Arşivle",
        "restore":"Geri Al", "restored":"Geri alındı.",
        "delete_permanent":"Kalıcı Sil", "deleted":"Kalıcı silindi.",
        "delete_confirm":"Emin misiniz? Bu işlem geri alınamaz.",
        "active_meetings":"Aktif Toplantılar", "confirmed_meetings":"Onaylı Toplantılar",
        "archived_meetings":"Arşiv / İptal", "no_meetings":"Toplantı yok.",
        "history":"Geçmiş", "no_history":"Geçmiş yok.",
        "status":"Durum", "entries":"Kayıt", "match_count":"Eşleşme", "people":"Kişi",
    }
}

# ── HELPERS ──────────────────────────────────────────────────────
def base_url():
    try: return st.context.url.split("?")[0]
    except: return "https://your-app.streamlit.app"

def q_code():
    try: return st.query_params.get("meeting", "")
    except: return ""

def card_open():
    st.markdown('<div class="card">', unsafe_allow_html=True)

def card_close():
    st.markdown('</div>', unsafe_allow_html=True)

def guide(txt):
    st.markdown(f'<div class="guide">{txt}</div>', unsafe_allow_html=True)

def empty(msg):
    st.markdown(f'<div class="empty"><h3>📭</h3><p>{msg}</p></div>', unsafe_allow_html=True)

def sbadge(status):
    return f'<span class="status-{status}">{status.upper()}</span>'

def pill(text, cls=""):
    c = f" {cls}" if cls else ""
    return f'<span class="pill{c}">{text}</span>'

def metrics_html(items):
    boxes = ""
    for num, lbl in items:
        boxes += f'<div class="metric-box"><div class="metric-num">{num}</div><div class="metric-lbl">{lbl}</div></div>'
    st.markdown(f'<div class="metric-row">{boxes}</div>', unsafe_allow_html=True)

def get_df(mc):
    rows = get_availability(mc)
    if not rows: return pd.DataFrame()
    return pd.DataFrame(rows, columns=["Name","Email","Role","Date","Start Time","End Time"])

def calc_matches(df, org_l, part_l):
    orgs = df[df["Role"]==org_l]
    parts = df[df["Role"]==part_l]
    out = []
    for _, o in orgs.iterrows():
        for _, p in parts.iterrows():
            if o["Date"]==p["Date"]:
                s = max(o["Start Time"], p["Start Time"])
                e = min(o["End Time"], p["End Time"])
                if s < e:
                    out.append({"Date":o["Date"],"Start":s,"End":e,
                                "Organizer":o["Name"],"Participant":p["Name"],
                                "Participant Email":p["Email"]})
    return out

def make_ics(title, date_s, start_s, end_s, desc="", video_link=""):
    start_s, end_s = str(start_s), str(end_s)
    if len(start_s)==5: start_s+=":00"
    if len(end_s)==5: end_s+=":00"
    s = datetime.strptime(f"{date_s} {start_s}", "%Y-%m-%d %H:%M:%S")
    e = datetime.strptime(f"{date_s} {end_s}", "%Y-%m-%d %H:%M:%S")
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    full_desc = desc
    if video_link:
        full_desc += f"\\nVideo Link: {video_link}"
    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MeetAlign//EN
BEGIN:VEVENT
UID:{stamp}@meetalign
DTSTAMP:{stamp}
DTSTART:{s.strftime("%Y%m%dT%H%M%S")}
DTEND:{e.strftime("%Y%m%dT%H%M%S")}
SUMMARY:{title}
DESCRIPTION:{full_desc}
LOCATION:{video_link}
END:VEVENT
END:VCALENDAR"""

def send_resend(to, subject, body):
    ak = st.secrets.get("RESEND_API_KEY","")
    se = st.secrets.get("SENDER_EMAIL","")
    if not ak or not se: return False, "RESEND_API_KEY/SENDER_EMAIL missing."
    try:
        r = requests.post("https://api.resend.com/emails",
            json={"from":se,"to":[to],"subject":subject,"html":body.replace("\n","<br>")},
            headers={"Authorization":f"Bearer {ak}","Content-Type":"application/json"}, timeout=30)
        return (r.status_code in [200,201,202]), r.text
    except Exception as ex: return False, str(ex)

def is_active(m):
    return m and m[2] == "active"

def is_blocked(m):
    if not m: return True
    return m[2] in ("cancelled","archived")

# ── SIDEBAR ──────────────────────────────────────────────────────
lang = st.sidebar.selectbox("Language / Dil", ["English","Türkçe"])
t = TEXT[lang]
qc = q_code()
st.sidebar.markdown("### 📅 MeetAlign")
menu = st.sidebar.radio(t["menu"],
    [t["create"], t["availability"], t["confirm"], t["chatbot"], t["manage"]],
    index=1 if qc else 0)

# ── HERO ─────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
    {pill("Availability")}{pill("Calendar","")} {pill("AI Chatbot","")} {pill("Zoom / Meet","pill-green")} {pill("Manage","pill-gray")}
    <div class="hero-title">📅 {t["title"]}</div>
    <div class="hero-sub">{t["subtitle"]}</div>
    <p style="margin-top:12px;font-size:16px;font-weight:600;color:#374151">{t["hero"]}</p>
</div>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════
# CREATE MEETING
# ═════════════════════════════════════════════════════════════════
if menu == t["create"]:
    st.header(f"🆕 {t['create']}")
    guide("1️⃣ Enter title → 2️⃣ Add video link (optional) → 3️⃣ Create → 4️⃣ Share")
    card_open()
    mt = st.text_input(t["meeting_title"], placeholder=t["meeting_placeholder"])
    vl = st.text_input(t["meeting_video_link"], placeholder=t["meeting_video_placeholder"])

    if st.button(t["create_button"], use_container_width=True):
        if not mt:
            st.warning(t["meeting_title"])
        else:
            mc = create_meeting(mt, vl)
            ml = f"{base_url()}?meeting={mc}"
            st.success(t["created"])
            c1, c2 = st.columns([1,2])
            with c1: st.text_input(t["meeting_code"], value=mc, disabled=True)
            with c2: st.text_input(t["meeting_link"], value=ml, disabled=True)

            if vl:
                st.markdown(f'<div class="link-box">🔗 Video: <a href="{vl}" target="_blank">{vl}</a></div>', unsafe_allow_html=True)

            st.subheader(t["copy_invitation"])
            video_line = f"\nVideo Link: {vl}" if vl else ""
            st.code(f"""Hello,

I created a meeting availability link for:
{mt}

Please add your availability:
{ml}

Meeting Code: {mc}{video_line}

Best regards""")
    card_close()

# ═════════════════════════════════════════════════════════════════
# ADD AVAILABILITY
# ═════════════════════════════════════════════════════════════════
elif menu == t["availability"]:
    st.header(f"📝 {t['availability']}")
    guide("1️⃣ Enter code → 2️⃣ Fill details → 3️⃣ Save")
    card_open()
    mc = st.text_input(t["meeting_code"], value=qc, placeholder="AB12CD34").strip().upper()
    meeting = get_meeting(mc) if mc else None

    if mc and not meeting:
        st.warning(t["not_found"])
    elif meeting:
        if is_blocked(meeting):
            st.error(t["blocked"])
            st.markdown(f"{t['status']}: {sbadge(meeting[2])}", unsafe_allow_html=True)
            card_close()
            st.stop()
        st.success(meeting[1])
        st.markdown(f"{t['status']}: {sbadge(meeting[2])}", unsafe_allow_html=True)
        if meeting[3]:
            st.markdown(f'<div class="link-box">🔗 <a href="{meeting[3]}" target="_blank">{meeting[3]}</a></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input(t["name"])
        email = st.text_input(t["email"])
    with c2:
        role = st.selectbox(t["role"], [t["organizer"], t["participant"]])
        date = st.date_input(t["date"])
        sc1, sc2 = st.columns(2)
        with sc1: start_time = st.time_input(t["start"])
        with sc2: end_time = st.time_input(t["end"])

    if st.button(t["save"], use_container_width=True):
        m2 = get_meeting(mc) if mc else None
        if not mc: st.warning(t["enter_code"])
        elif not m2: st.warning(t["not_found"])
        elif is_blocked(m2): st.error(t["blocked"])
        elif not name: st.warning(t["enter_name"])
        elif start_time >= end_time: st.warning(t["time_error"])
        else:
            add_availability(mc, name, email, role, date, start_time, end_time)
            st.success(t["saved"])
    card_close()

# ═════════════════════════════════════════════════════════════════
# CONFIRM & CALENDAR
# ═════════════════════════════════════════════════════════════════
elif menu == t["confirm"]:
    st.header(f"✅ {t['confirm']}")
    guide("1️⃣ Enter code → 2️⃣ View matches → 3️⃣ Confirm → 4️⃣ Download .ics / Send email")
    card_open()
    mc = st.text_input(t["meeting_code"], value=qc, key="conf_mc").strip().upper()
    meeting = get_meeting(mc) if mc else None

    if not mc:
        st.info(t["enter_code"]); card_close(); st.stop()
    if not meeting:
        st.warning(t["not_found"]); card_close(); st.stop()
    if is_blocked(meeting):
        st.error(t["blocked"]); card_close(); st.stop()

    mtitle = meeting[1]
    mstatus = meeting[2]
    vlink = meeting[3]

    st.success(mtitle)
    st.markdown(f"{t['status']}: {sbadge(mstatus)}", unsafe_allow_html=True)

    # Video link section
    st.markdown(f"### 🔗 {t['video_link']}")
    if vlink:
        st.markdown(f'<div class="link-box">🎥 <a href="{vlink}" target="_blank">{vlink}</a></div>', unsafe_allow_html=True)
    else:
        st.info(t["no_video_link"])

    new_link = st.text_input(t["meeting_video_link"], value=vlink or "", key="update_vl",
                             placeholder=t["meeting_video_placeholder"])
    if st.button(t["update_link"], key="btn_upd_link"):
        update_meeting_link(mc, new_link)
        st.success(t["link_updated"])
        st.rerun()

    # Already confirmed
    if mstatus == "confirmed":
        st.info(f"{t['already_confirmed']}: {meeting[4]} | {meeting[5]} - {meeting[6]}")
        ics = make_ics(mtitle, meeting[4], meeting[5], meeting[6],
                       f"MeetAlign Code: {mc}", vlink)
        st.download_button(t["download_ics"], data=ics,
                           file_name=f"meetalign_{mc}.ics", mime="text/calendar",
                           use_container_width=True)

    df = get_df(mc)
    if df.empty:
        empty(t["no_data"]); card_close(); st.stop()

    st.subheader(t["all_availability"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    matches = calc_matches(df, t["organizer"], t["participant"])
    st.subheader(t["matches"])

    if not matches:
        empty(t["no_match"]); card_close(); st.stop()

    metrics_html([(len(df), t["entries"]), (len(matches), t["match_count"]),
                  (df["Email"].nunique(), t["people"])])

    st.dataframe(pd.DataFrame(matches), use_container_width=True, hide_index=True)

    # AI Invitation Email
    if st.button(t["generate_invite"], key="gen_inv"):
        inv_email = generate_meeting_email(mtitle, matches, language=lang, meeting_link=vlink)
        st.subheader(t["generated_email"])
        st.text_area("", value=inv_email, height=250, key="inv_ta")

    si = st.selectbox(t["select_slot"], range(len(matches)),
        format_func=lambda i: f"{matches[i]['Date']} | {matches[i]['Start']} - {matches[i]['End']}")
    sel = matches[si]

    st.markdown(f"### ✅ **{sel['Date']}** | **{sel['Start']}** – **{sel['End']}**")

    if mstatus != "confirmed":
        if st.button(t["confirm_meeting"], use_container_width=True):
            confirm_meeting_slot(mc, sel["Date"], sel["Start"], sel["End"])
            st.success(t["confirmed"])
            ics = make_ics(mtitle, sel["Date"], sel["Start"], sel["End"],
                           f"MeetAlign Code: {mc}", vlink)
            st.download_button(t["download_ics"], data=ics,
                               file_name=f"meetalign_{mc}.ics", mime="text/calendar",
                               use_container_width=True)

    # AI Confirmation Email + Send
    st.markdown("### ✉️ AI Confirmation Email")
    re = st.text_input(t["recipient_email"], value=sel.get("Participant Email",""), key="conf_re")

    if st.button("Generate AI Confirmation Email", key="gen_conf_email"):
        ai_body = generate_confirmation_email(mtitle, sel["Date"], sel["Start"], sel["End"],
                                              language=lang, meeting_link=vlink)
        st.session_state["conf_email_body"] = ai_body

    email_body = st.text_area("Email Preview",
        value=st.session_state.get("conf_email_body", "Click 'Generate AI Confirmation Email' above."),
        height=200, key="conf_email_ta")

    if st.button(t["send_email"], use_container_width=True, key="btn_send_conf"):
        if not re: st.warning(t["recipient_email"])
        else:
            ok, msg = send_resend(re, f"Confirmed: {mtitle}", email_body)
            if ok: st.success(t["email_sent"])
            else: st.error(f"{t['email_failed']} {msg}")
    card_close()

# ═════════════════════════════════════════════════════════════════
# AI CHATBOT
# ═════════════════════════════════════════════════════════════════
elif menu == t["chatbot"]:
    st.header(f"🤖 {t['chatbot']}")
    guide(t["chat_help"])
    card_open()

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    mode = st.radio(t["chat_mode"], [t["mode_command"], t["mode_chat"]], horizontal=True)

    for ch in st.session_state["chat_history"]:
        icon = "🧑" if ch["role"]=="user" else "🤖"
        st.markdown(f"**{icon}** {ch['text']}")
        st.markdown("---")

    um = st.text_area(t["chat_input"], height=120, placeholder=t["chat_help"])

    if st.button(t["chat_button"], use_container_width=True):
        if not um: st.warning(t["chat_input"])
        else:
            st.session_state["chat_history"].append({"role":"user","text":um})
            if mode == t["mode_chat"]:
                reply = ai_chatbot_response(um, language=lang)
                st.session_state["chat_history"].append({"role":"ai","text":reply})
                st.rerun()
            else:
                parsed, err = parse_meeting_command(um)
                if err:
                    st.error(err)
                    st.session_state["chat_history"].append({"role":"ai","text":f"Error: {err}"})
                else:
                    st.subheader(t["parsed"])
                    st.json(parsed)
                    mt2 = parsed.get("meeting_title") or "MeetAlign Meeting"
                    dv = parsed.get("date","")
                    stv = parsed.get("start_time","")
                    etv = parsed.get("end_time","")
                    pn = parsed.get("participant_name","")
                    if stv and not etv:
                        try:
                            tmp = datetime.strptime(stv,"%H:%M")
                            etv = (tmp+timedelta(minutes=30)).strftime("%H:%M")
                        except: etv = ""
                    mc2 = create_meeting(mt2)
                    ml2 = f"{base_url()}?meeting={mc2}"
                    st.success(t["created"])
                    c1, c2 = st.columns([1,2])
                    with c1: st.text_input(t["meeting_code"], value=mc2, key="ch_mc", disabled=True)
                    with c2: st.text_input(t["meeting_link"], value=ml2, key="ch_ml", disabled=True)
                    if dv and stv and etv:
                        add_availability(mc2,"Organizer","",t["organizer"],dv,
                            f"{stv}:00" if len(stv)==5 else stv,
                            f"{etv}:00" if len(etv)==5 else etv)
                        st.info("Organizer availability added.")
                    st.subheader(t["copy_invitation"])
                    st.code(f"""Hello {pn},

Meeting: {mt2}
Link: {ml2}
Code: {mc2}

Best regards""")
                    st.session_state["chat_history"].append(
                        {"role":"ai","text":f"Created: {mt2} | Code: {mc2}"})
    card_close()

# ═════════════════════════════════════════════════════════════════
# MANAGE MEETINGS
# ═════════════════════════════════════════════════════════════════
elif menu == t["manage"]:
    st.header(f"⚙️ {t['manage']}")
    guide("View, cancel, archive, restore or permanently delete meetings.")

    # ── Active Meetings ──
    card_open()
    st.subheader(f"🟢 {t['active_meetings']}")
    actives = get_active_meetings()
    if not actives:
        empty(t["no_meetings"])
    else:
        for m in actives:
            st.markdown(f"""<div class="meeting-row">
                <div><strong>{m[1]}</strong> &nbsp; <code>{m[0]}</code> &nbsp; {sbadge(m[2])}</div>
                <div style="color:#9ca3af;font-size:13px">{m[3]}</div>
            </div>""", unsafe_allow_html=True)
    card_close()

    # ── Confirmed Meetings ──
    card_open()
    st.subheader(f"🔵 {t['confirmed_meetings']}")
    confirmed = get_confirmed_meetings()
    if not confirmed:
        empty(t["no_meetings"])
    else:
        for m in confirmed:
            st.markdown(f"""<div class="meeting-row">
                <div><strong>{m[1]}</strong> &nbsp; <code>{m[0]}</code> &nbsp; {sbadge(m[2])}</div>
                <div style="color:#9ca3af;font-size:13px">{m[3]}</div>
            </div>""", unsafe_allow_html=True)
    card_close()

    # ── Archived / Cancelled ──
    card_open()
    st.subheader(f"📦 {t['archived_meetings']}")
    archived = get_archived_meetings()
    if not archived:
        empty(t["no_meetings"])
    else:
        for a in archived:
            reason_txt = f" — {a[4]}" if a[4] else ""
            st.markdown(f"""<div class="meeting-row" style="border-color:#fecaca">
                <div><strong>{a[1]}</strong> &nbsp; <code>{a[0]}</code>{reason_txt}</div>
                <div style="color:#9ca3af;font-size:13px">{a[3]}</div>
            </div>""", unsafe_allow_html=True)
    card_close()

    # ── Actions ──
    card_open()
    st.subheader("🔧 Actions")
    mc_m = st.text_input(t["meeting_code"], key="manage_mc", placeholder="AB12CD34").strip().upper()
    meeting = get_meeting(mc_m) if mc_m else None

    if mc_m and not meeting:
        st.warning(t["not_found"])
    elif meeting:
        st.success(f"{meeting[1]}")
        st.markdown(f"{t['status']}: {sbadge(meeting[2])}", unsafe_allow_html=True)

        if meeting[3]:
            st.markdown(f'<div class="link-box">🔗 <a href="{meeting[3]}" target="_blank">{meeting[3]}</a></div>', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if meeting[2] == "active":
                reason = st.text_input(t["cancel_reason"], key="m_reason")
                if st.button(f"🚫 {t['cancel']}", use_container_width=True, key="btn_cancel"):
                    cancel_meeting(mc_m, reason)
                    st.warning(t["cancelled"])
                    st.rerun()

        with col2:
            if meeting[2] == "active":
                if st.button(f"📦 {t['archive']}", use_container_width=True, key="btn_archive"):
                    archive_meeting(mc_m)
                    st.info("Archived.")
                    st.rerun()

        with col3:
            if meeting[2] in ("cancelled","archived"):
                if st.button(f"♻️ {t['restore']}", use_container_width=True, key="btn_restore"):
                    restore_meeting(mc_m)
                    st.success(t["restored"])
                    st.rerun()

        with col4:
            if meeting[2] in ("cancelled","archived"):
                st.caption(t["delete_confirm"])
                if st.button(f"🗑️ {t['delete_permanent']}", use_container_width=True, key="btn_del"):
                    delete_meeting_permanent(mc_m)
                    st.error(t["deleted"])
                    st.rerun()

        # History
        st.markdown("---")
        st.subheader(f"📜 {t['history']}")
        hist = get_meeting_history(mc_m)
        if hist:
            for h in hist:
                st.markdown(f'<div class="history-item"><strong>{h[0]}</strong> — {h[1]}<br>'
                            f'<small style="color:#9ca3af">{h[2]}</small></div>', unsafe_allow_html=True)
        else:
            empty(t["no_history"])
    card_close()
