import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from database import (
    init_db, create_meeting, get_meeting, update_meeting_link,
    add_availability, get_availability, cancel_meeting, archive_meeting,
    restore_meeting, confirm_meeting_slot, delete_meeting_permanent,
    get_meeting_history, get_all_meetings, get_active_meetings,
    get_archived_meetings, get_confirmed_meetings, postpone_meeting,
    create_proposal, get_proposals, get_pending_proposals,
    get_all_pending_proposals, update_proposal, get_meeting_stats
)
from ai_assistant import (
    parse_meeting_command, generate_meeting_email,
    generate_confirmation_email, ai_chatbot_response,
    suggest_alternative_dates, generate_proposal_email
)

init_db()
ADMIN_PASSWORD = "1234"

st.set_page_config(
    page_title="MeetAlign",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════
# CSS — Geliştirilmiş
# ═══════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    :root{--blue:#2563eb;--indigo:#4f46e5;--green:#16a34a;--red:#dc2626;
          --amber:#d97706;--gray:#6b7280;--purple:#7c3aed;--light:#f8fafc;--white:#ffffff}
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
    .pill-purple{background:#f5f3ff;color:var(--purple);border-color:#ddd6fe}

    .empty{background:linear-gradient(135deg,#fff 0%,#f8fafc 100%);padding:40px;border-radius:24px;
           border:2px dashed #cbd5e1;text-align:center;color:#94a3b8;margin-top:20px}
    .empty h3{font-size:40px;margin-bottom:8px}.empty p{font-size:15px}

    .metric-row{display:flex;gap:16px;margin:20px 0;flex-wrap:wrap}
    .metric-box{flex:1;min-width:120px;background:linear-gradient(135deg,#fff 0%,#f8fafc 100%);padding:22px;border-radius:20px;
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
    .status-pending{color:var(--amber);font-weight:700}

    .proposal-card{padding:16px 20px;border-radius:16px;border:1px solid #fde68a;margin-bottom:12px;
                   background:linear-gradient(135deg,#fffbeb 0%,#fef3c7 100%);transition:all .15s}
    .proposal-card:hover{box-shadow:0 6px 20px rgba(217,119,6,.1)}
    .proposal-accepted{border-color:#bbf7d0;background:linear-gradient(135deg,#f0fdf4 0%,#dcfce7 100%)}
    .proposal-rejected{border-color:#fecaca;background:linear-gradient(135deg,#fef2f2 0%,#fee2e2 100%)}

    .suggestion-box{background:linear-gradient(135deg,#f5f3ff 0%,#ede9fe 100%);border:1px solid #ddd6fe;
                    border-radius:18px;padding:22px;margin:16px 0}
    .suggestion-title{font-size:16px;font-weight:700;color:var(--purple);margin-bottom:10px}

    .notification-badge{background:var(--red);color:#fff;border-radius:50%;padding:2px 8px;
                        font-size:11px;font-weight:800;margin-left:6px}

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
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# TEXT — İki dil desteği
# ═══════════════════════════════════════════════════════
TEXT = {
    "English": {
        "menu":"Workspace","dashboard":"Dashboard","create":"Create Meeting",
        "availability":"Add Availability","negotiate":"Negotiate & Propose",
        "confirm":"Confirm & Calendar","chatbot":"AI Chatbot","manage":"Manage Meetings",
        "title":"MeetAlign",
        "subtitle":"Smart meeting scheduler for project teams, researchers and consortium partners.",
        "hero":"Create → Collect availability → Negotiate → Confirm → Send invite",
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
        "no_data":"No availability yet.","no_match":"No matching slots found.",
        "select_slot":"Select slot","confirm_meeting":"✅ Confirm This Slot",
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
        "propose_new":"📨 Propose New Date","propose_hint":"No match? Suggest a time that works for you.",
        "proposals":"📨 Date Proposals","pending":"Pending","accepted":"Accepted",
        "rejected":"Rejected","accept":"✅ Accept","reject":"❌ Reject",
        "counter":"🔄 Counter-Propose","no_proposals":"No proposals yet.",
        "ai_suggest":"🤖 AI Suggestions","ai_suggest_btn":"🤖 Get AI Suggestions",
        "near_misses":"🔍 Near Misses","postpone":"⏸️ Postpone","postpone_reason":"Postpone reason",
        "postponed":"Meeting postponed. Collecting new availability.",
        "reschedule":"🔄 Reschedule","total":"Total","pending_proposals":"Pending Proposals",
        "response_note":"Note (optional)","propose_button":"📨 Send Proposal",
        "proposal_sent":"✅ Proposal sent!","proposal_accepted":"✅ Proposal accepted!",
        "proposal_rejected":"❌ Proposal rejected.","propose_date":"Proposed Date",
        "propose_start":"Proposed Start","propose_end":"Proposed End",
        "confirm_from_proposal":"✅ Accept & Confirm Meeting",
        "no_match_help":"💡 No overlapping times found. You can:\n1. Ask AI for suggestions\n2. Propose a new time\n3. Add more availability slots",
    },
    "Türkçe": {
        "menu":"Çalışma Alanı","dashboard":"Gösterge Paneli","create":"Toplantı Oluştur",
        "availability":"Uygunluk Ekle","negotiate":"Müzakere & Teklif",
        "confirm":"Onayla & Takvim","chatbot":"AI Chatbot","manage":"Toplantı Yönetimi",
        "title":"MeetAlign",
        "subtitle":"Proje ekipleri ve araştırmacılar için akıllı toplantı planlayıcı.",
        "hero":"Oluştur → Uygunluk topla → Müzakere → Onayla → Davet gönder",
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
        "no_data":"Henüz uygunluk yok.","no_match":"Eşleşen zaman dilimi bulunamadı.",
        "select_slot":"Saat seçin","confirm_meeting":"✅ Bu Saati Onayla",
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
        "propose_new":"📨 Yeni Tarih Öner","propose_hint":"Eşleşme yok mu? Size uygun bir zaman önerin.",
        "proposals":"📨 Tarih Teklifleri","pending":"Bekliyor","accepted":"Kabul Edildi",
        "rejected":"Reddedildi","accept":"✅ Kabul Et","reject":"❌ Reddet",
        "counter":"🔄 Karşı Teklif","no_proposals":"Henüz teklif yok.",
        "ai_suggest":"🤖 AI Önerileri","ai_suggest_btn":"🤖 AI Önerisi Al",
        "near_misses":"🔍 Yakın Eşleşmeler","postpone":"⏸️ Ertele","postpone_reason":"Erteleme nedeni",
        "postponed":"Toplantı ertelendi. Yeni uygunluklar toplanıyor.",
        "reschedule":"🔄 Yeniden Planla","total":"Toplam","pending_proposals":"Bekleyen Teklifler",
        "response_note":"Not (opsiyonel)","propose_button":"📨 Teklif Gönder",
        "proposal_sent":"✅ Teklif gönderildi!","proposal_accepted":"✅ Teklif kabul edildi!",
        "proposal_rejected":"❌ Teklif reddedildi.","propose_date":"Önerilen Tarih",
        "propose_start":"Önerilen Başlangıç","propose_end":"Önerilen Bitiş",
        "confirm_from_proposal":"✅ Kabul Et & Toplantıyı Onayla",
        "no_match_help":"💡 Örtüşen zaman bulunamadı. Şunları yapabilirsiniz:\n1. AI'dan öneri isteyin\n2. Yeni zaman teklif edin\n3. Daha fazla uygunluk ekleyin",
    }
}

# ═══════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════
def base_url():
    try:
        return st.context.url.split("?")[0]
    except:
        return "https://your-app.streamlit.app"

def q_code():
    try:
        return st.query_params.get("meeting", "")
    except:
        return ""

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
    b = "".join(
        f'<div class="metric-box"><div class="metric-num">{n}</div><div class="metric-lbl">{l}</div></div>'
        for n, l in items
    )
    st.markdown(f'<div class="metric-row">{b}</div>', unsafe_allow_html=True)

def mchtml(code, title, status, dt=""):
    return f"""<div class="meeting-card"><div style="display:flex;justify-content:space-between;align-items:center">
        <div><span class="meeting-card-title">{title}</span>&nbsp;&nbsp;
        <span class="meeting-card-code">{code}</span>&nbsp;&nbsp;{sbadge(status)}</div>
        <div class="meeting-card-date">{dt}</div></div></div>"""

def get_df(mc):
    rows = get_availability(mc)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows, columns=["Name", "Email", "Role", "Date", "Start Time", "End Time"])

def calc_matches(df, ol, pl):
    orgs = df[df["Role"] == ol]
    parts = df[df["Role"] == pl]
    out = []
    for _, o in orgs.iterrows():
        for _, p in parts.iterrows():
            if o["Date"] == p["Date"]:
                s = max(o["Start Time"], p["Start Time"])
                e = min(o["End Time"], p["End Time"])
                if s < e:
                    out.append({
                        "Date": o["Date"], "Start": s, "End": e,
                        "Organizer": o["Name"], "Participant": p["Name"],
                        "Participant Email": p["Email"]
                    })
    return out

def calc_near_misses(df, ol, pl):
    """Aynı tarihte ama örtüşmeyen saatleri bul."""
    orgs = df[df["Role"] == ol]
    parts = df[df["Role"] == pl]
    near = []
    for _, o in orgs.iterrows():
        for _, p in parts.iterrows():
            if o["Date"] == p["Date"]:
                s = max(o["Start Time"], p["Start Time"])
                e = min(o["End Time"], p["End Time"])
                if s >= e:  # Örtüşme yok
                    gap_minutes = 0
                    try:
                        # Yakınlığı hesapla
                        os_dt = datetime.strptime(str(o["Start Time"])[:5], "%H:%M")
                        oe_dt = datetime.strptime(str(o["End Time"])[:5], "%H:%M")
                        ps_dt = datetime.strptime(str(p["Start Time"])[:5], "%H:%M")
                        pe_dt = datetime.strptime(str(p["End Time"])[:5], "%H:%M")
                        gap1 = abs((ps_dt - oe_dt).total_seconds() / 60)
                        gap2 = abs((os_dt - pe_dt).total_seconds() / 60)
                        gap_minutes = min(gap1, gap2)
                    except:
                        gap_minutes = 999
                    near.append({
                        "Date": o["Date"],
                        "Org_Name": o["Name"], "Org_Start": o["Start Time"], "Org_End": o["End Time"],
                        "Part_Name": p["Name"], "Part_Start": p["Start Time"], "Part_End": p["End Time"],
                        "Gap_Min": round(gap_minutes)
                    })
    # Yakınlığa göre sırala
    near.sort(key=lambda x: x["Gap_Min"])
    return near

def make_ics(title, ds, ss, es, desc="", vl=""):
    ss, es = str(ss), str(es)
    if len(ss) == 5:
        ss += ":00"
    if len(es) == 5:
        es += ":00"
    s = datetime.strptime(f"{ds} {ss}", "%Y-%m-%d %H:%M:%S")
    e = datetime.strptime(f"{ds} {es}", "%Y-%m-%d %H:%M:%S")
    st_ = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    fd = desc + (f"\\nVideo: {vl}" if vl else "")
    return (
        f"BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//MeetAlign//EN\nBEGIN:VEVENT\n"
        f"UID:{st_}@meetalign\nDTSTAMP:{st_}\n"
        f"DTSTART:{s.strftime('%Y%m%dT%H%M%S')}\nDTEND:{e.strftime('%Y%m%dT%H%M%S')}\n"
        f"SUMMARY:{title}\nDESCRIPTION:{fd}\nLOCATION:{vl}\n"
        f"END:VEVENT\nEND:VCALENDAR"
    )

def send_resend(to, subj, body):
    ak = st.secrets.get("RESEND_API_KEY", "")
    se = st.secrets.get("SENDER_EMAIL", "")
    if not ak or not se:
        return False, "RESEND keys missing."
    try:
        r = requests.post(
            "https://api.resend.com/emails",
            json={"from": se, "to": [to], "subject": subj, "html": body.replace("\n", "<br>")},
            headers={"Authorization": f"Bearer {ak}", "Content-Type": "application/json"},
            timeout=30
        )
        return (r.status_code in [200, 201, 202]), r.text
    except Exception as ex:
        return False, str(ex)

def is_blocked(m):
    if not m:
        return True
    return m[2] in ("cancelled", "archived")

def check_admin():
    return st.session_state.get("admin_auth", False)

def all_meetings_for_select():
    a = get_active_meetings()
    c = get_confirmed_meetings()
    return a + c

def all_meetings_for_manage():
    return get_all_meetings()

def get_slots_for_ai(df, role_label):
    """DataFrame'den AI için slot listesi oluştur."""
    filtered = df[df["Role"] == role_label]
    slots = []
    for _, row in filtered.iterrows():
        slots.append({
            "Date": row["Date"],
            "Start": str(row["Start Time"]),
            "End": str(row["End Time"]),
            "Name": row["Name"]
        })
    return slots


# ═══════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════
lang = st.sidebar.selectbox("🌐 Language / Dil", ["English", "Türkçe"])
t = TEXT[lang]
qc = q_code()

st.sidebar.markdown("---")
st.sidebar.markdown("### 📅 MeetAlign")
st.sidebar.caption(t["subtitle"])
st.sidebar.markdown("---")

# Bekleyen teklif sayısı
pending_count = len(get_all_pending_proposals())
negotiate_label = t["negotiate"]
if pending_count > 0:
    negotiate_label = f'{t["negotiate"]} 🔴 {pending_count}'

menu_items = [
    t["dashboard"], t["create"], t["availability"],
    negotiate_label, t["confirm"], t["chatbot"], t["manage"]
]

default_menu_idx = 0
if qc:
    default_menu_idx = 2  # Availability

menu = st.sidebar.radio(t["menu"], menu_items, index=default_menu_idx)

if check_admin():
    st.sidebar.markdown("---")
    if st.sidebar.button("🔒 Logout Admin", key="sb_logout"):
        st.session_state["admin_auth"] = False
        st.rerun()

# Sidebar'da hızlı istatistik
st.sidebar.markdown("---")
stats = get_meeting_stats()
st.sidebar.markdown(f"""
**📊 Quick Stats**
- 📋 Total: **{stats['total']}**
- 🟢 Active: **{stats['active']}**
- 🔵 Confirmed: **{stats['confirmed']}**
- 📨 Pending: **{stats['pending_proposals']}**
""")


# ═══════════════════════════════════════════════════════
# HERO
# ═══════════════════════════════════════════════════════
st.markdown(f"""<div class="hero">
    {pill_html("📋 Availability")} {pill_html("📅 Calendar")} {pill_html("🤖 AI")}
    {pill_html("🎥 Zoom/Meet","pill-green")} {pill_html("📨 Negotiate","pill-purple")}
    {pill_html("⚙️ Admin","pill-gray")}
    <div class="hero-title">📅 {t["title"]}</div>
    <div class="hero-sub">{t["subtitle"]}</div>
    <div class="hero-steps">{t["hero"]}</div>
</div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# 0. DASHBOARD
# ═══════════════════════════════════════════════════════
if menu == t["dashboard"]:
    st.header(f"📊 {t['dashboard']}")

    stats = get_meeting_stats()
    metrics_html([
        (stats["total"], t["total"]),
        (stats["active"], t["active_meetings"]),
        (stats["confirmed"], t["confirmed_meetings"]),
        (stats["pending_proposals"], t["pending_proposals"]),
    ])

    # Bekleyen teklifler uyarısı
    pending_props = get_all_pending_proposals()
    if pending_props:
        card_open()
        st.markdown(f'<div class="section-head">🔔 {t["pending_proposals"]} ({len(pending_props)})</div>', unsafe_allow_html=True)
        for pp in pending_props:
            st.markdown(
                f'<div class="proposal-card">'
                f'<strong>{pp[2]}</strong> — <code>{pp[1]}</code><br>'
                f'📨 {pp[3]} proposed: <strong>{pp[4]}</strong> | {pp[5]}-{pp[6]}<br>'
                f'<small style="color:#94a3b8">{pp[7]}</small></div>',
                unsafe_allow_html=True
            )
        card_close()

    # Son toplantılar
    card_open()
    st.markdown(f'<div class="section-head">{t["existing_meetings"]}</div>', unsafe_allow_html=True)
    all_m = get_all_meetings()
    if all_m:
        for m in all_m[:10]:
            st.markdown(mchtml(m[0], m[1], m[2], m[3]), unsafe_allow_html=True)
    else:
        empty(t["no_meetings"])
    card_close()


# ═══════════════════════════════════════════════════════
# 1. CREATE MEETING
# ═══════════════════════════════════════════════════════
elif menu == t["create"]:
    st.header(f"🆕 {t['create']}")
    guide("1️⃣ Title & video link → 2️⃣ Your availability → 3️⃣ Create → 4️⃣ Share")

    card_open()
    st.markdown('<div class="section-head">📝 Meeting Details</div>', unsafe_allow_html=True)
    mt = st.text_input(t["meeting_title"], placeholder=t["meeting_placeholder"])
    vl = st.text_input(t["meeting_video_link"], placeholder=t["meeting_video_placeholder"])

    divider()
    st.markdown(f'<div class="section-head">{t["org_info"]}</div>', unsafe_allow_html=True)
    oc1, oc2 = st.columns(2)
    with oc1:
        org_name = st.text_input(t["org_name"], placeholder="John Doe")
        org_email = st.text_input(t["org_email"], placeholder="john@example.com")
    with oc2:
        org_date = st.date_input(t["org_date"])
        osc1, osc2 = st.columns(2)
        with osc1:
            org_start = st.time_input(t["org_start"], key="cr_os")
        with osc2:
            org_end = st.time_input(t["org_end"], key="cr_oe")

    # Birden fazla uygunluk ekleme
    divider()
    st.markdown("**➕ Add more availability slots (optional)**")

    if "extra_org_slots" not in st.session_state:
        st.session_state["extra_org_slots"] = []

    if st.button("➕ Add Another Time Slot", key="add_extra_slot"):
        st.session_state["extra_org_slots"].append({})

    extra_slots = []
    for idx, _ in enumerate(st.session_state["extra_org_slots"]):
        with st.expander(f"📅 Extra Slot #{idx + 1}", expanded=True):
            ec1, ec2 = st.columns(2)
            with ec1:
                ed = st.date_input(f"Date #{idx+1}", key=f"cr_ed_{idx}")
            with ec2:
                esc1, esc2 = st.columns(2)
                with esc1:
                    es_t = st.time_input(f"Start #{idx+1}", key=f"cr_es_{idx}")
                with esc2:
                    ee_t = st.time_input(f"End #{idx+1}", key=f"cr_ee_{idx}")
            extra_slots.append({"date": ed, "start": es_t, "end": ee_t})

    st.markdown("")
    if st.button(t["create_button"], use_container_width=True):
        if not mt:
            st.warning(t["meeting_title"])
        elif not org_name:
            st.warning(t["enter_name"])
        elif org_start >= org_end:
            st.warning(t["time_error"])
        else:
            mc = create_meeting(mt, vl)
            ml = f"{base_url()}?meeting={mc}"
            add_availability(mc, org_name, org_email, t["organizer"], org_date, org_start, org_end)

            # Ekstra slotlar
            for es in extra_slots:
                if es["start"] < es["end"]:
                    add_availability(mc, org_name, org_email, t["organizer"], es["date"], es["start"], es["end"])

            st.session_state["extra_org_slots"] = []
            st.success(t["created"])

            c1, c2 = st.columns([1, 2])
            with c1:
                st.text_input(t["meeting_code"], value=mc, disabled=True, key="cr_mc")
            with c2:
                st.text_input(t["meeting_link"], value=ml, disabled=True, key="cr_ml")

            if vl:
                st.markdown(f'<div class="link-box">🎥 <a href="{vl}" target="_blank">{vl}</a></div>', unsafe_allow_html=True)

            slot_info = f"📅 {org_date} | {org_start}-{org_end}"
            for es in extra_slots:
                if es["start"] < es["end"]:
                    slot_info += f"\n📅 {es['date']} | {es['start']}-{es['end']}"
            st.info(f"👤 {org_name}\n{slot_info}")

            divider()
            st.subheader(t["copy_invitation"])
            vline = f"\nVideo: {vl}" if vl else ""
            st.code(f"""Hello,\n\nMeeting: {mt}\nLink: {ml}\nCode: {mc}{vline}\n\nOrganizer: {org_name}\n{slot_info}\n\nBest regards""")
    card_close()


# ═══════════════════════════════════════════════════════
# 2. ADD AVAILABILITY
# ═══════════════════════════════════════════════════════
elif menu == t["availability"]:
    st.header(f"📝 {t['availability']}")
    guide("1️⃣ Select meeting → 2️⃣ Fill details → 3️⃣ Save (add multiple slots!)")

    avail_list = all_meetings_for_select()

    card_open()
    st.markdown(f'<div class="section-head">{t["existing_meetings"]}</div>', unsafe_allow_html=True)

    if avail_list:
        for m in avail_list:
            st.markdown(mchtml(m[0], m[1], m[2], m[3]), unsafe_allow_html=True)
    else:
        empty(t["no_meetings"])

    options_codes = [m[0] for m in avail_list] if avail_list else []
    options_labels = {m[0]: f"📋 {m[0]} — {m[1]}" for m in avail_list} if avail_list else {}

    default_idx = 0
    if qc and qc.upper() in [c.upper() for c in options_codes]:
        for i, c in enumerate(options_codes):
            if c.upper() == qc.upper():
                default_idx = i + 1
                break

    sel_options = [""] + options_codes
    sel_meeting = st.selectbox(
        t["select_meeting"], sel_options,
        index=default_idx,
        format_func=lambda x: options_labels.get(x, f"— {t['enter_code']} —") if x else f"— {t['enter_code']} —",
        key="avail_sel"
    )

    mc = sel_meeting.strip().upper() if sel_meeting else ""
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

        edf = get_df(mc)
        if not edf.empty:
            divider()
            st.markdown(f'<div class="section-head">📊 {t["all_availability"]}</div>', unsafe_allow_html=True)
            metrics_html([(len(edf), t["entries"]), (edf["Email"].nunique(), t["people"])])
            st.dataframe(edf, use_container_width=True, hide_index=True)

            # Eşleşmeleri hemen göster
            matches = calc_matches(edf, t["organizer"], t["participant"])
            if matches:
                st.markdown(f'<div class="section-head">✅ {t["matches"]} ({len(matches)})</div>', unsafe_allow_html=True)
                for m in matches:
                    st.markdown(
                        f'{pill_html(m["Date"],"pill-green")} '
                        f'{pill_html(f"{m[\"Start\"]}-{m[\"End\"]}","pill-green")} '
                        f'{m["Organizer"]} ↔ {m["Participant"]}',
                        unsafe_allow_html=True
                    )
            else:
                st.warning(t["no_match"])
                # Yakın eşleşmeler
                near = calc_near_misses(edf, t["organizer"], t["participant"])
                if near:
                    st.markdown(f'<div class="section-head">{t["near_misses"]}</div>', unsafe_allow_html=True)
                    for n in near[:5]:
                        gap_text = f"({n['Gap_Min']} min gap)" if n['Gap_Min'] < 999 else ""
                        st.markdown(
                            f"📅 **{n['Date']}**: {n['Org_Name']} {n['Org_Start']}-{n['Org_End']} | "
                            f"{n['Part_Name']} {n['Part_Start']}-{n['Part_End']} {gap_text}"
                        )

        divider()
        st.markdown('<div class="section-head">➕ Add Your Availability</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input(t["name"], key="av_name")
            email = st.text_input(t["email"], key="av_email")
        with c2:
            role = st.selectbox(t["role"], [t["organizer"], t["participant"]], key="av_role")
            date = st.date_input(t["date"], key="av_date")
            sc1, sc2 = st.columns(2)
            with sc1:
                start_time = st.time_input(t["start"], key="av_st")
            with sc2:
                end_time = st.time_input(t["end"], key="av_et")

        # Birden fazla slot
        if "avail_extra_slots" not in st.session_state:
            st.session_state["avail_extra_slots"] = []

        if st.button("➕ Add Another Slot", key="av_add_extra"):
            st.session_state["avail_extra_slots"].append({})

        av_extras = []
        for idx, _ in enumerate(st.session_state["avail_extra_slots"]):
            with st.expander(f"📅 Extra Slot #{idx + 1}", expanded=True):
                aec1, aec2 = st.columns(2)
                with aec1:
                    aed = st.date_input(f"Date #{idx+1}", key=f"av_ed_{idx}")
                with aec2:
                    aes1, aes2 = st.columns(2)
                    with aes1:
                        aes_t = st.time_input(f"Start #{idx+1}", key=f"av_es_{idx}")
                    with aes2:
                        aee_t = st.time_input(f"End #{idx+1}", key=f"av_ee_{idx}")
                av_extras.append({"date": aed, "start": aes_t, "end": aee_t})

        st.markdown("")
        if st.button(t["save"], use_container_width=True, key="av_save"):
            if not name:
                st.warning(t["enter_name"])
            elif start_time >= end_time:
                st.warning(t["time_error"])
            else:
                add_availability(mc, name, email, role, date, start_time, end_time)
                for es in av_extras:
                    if es["start"] < es["end"]:
                        add_availability(mc, name, email, role, es["date"], es["start"], es["end"])
                st.session_state["avail_extra_slots"] = []
                st.success(t["saved"])
                st.rerun()
        card_close()
    elif not mc:
        st.info(t["enter_code"])


# ═══════════════════════════════════════════════════════
# 3. NEGOTIATE & PROPOSE (YENİ SAYFA)
# ═══════════════════════════════════════════════════════
elif menu == negotiate_label:
    st.header(f"📨 {t['negotiate']}")
    guide("🔄 No match? Get AI suggestions, propose alternative dates, or accept proposals.")

    avail_list = all_meetings_for_select()
    card_open()

    options_codes = [m[0] for m in avail_list] if avail_list else []
    options_labels = {m[0]: f"📋 {m[0]} — {m[1]}" for m in avail_list} if avail_list else {}

    default_idx = 0
    if qc and qc.upper() in [c.upper() for c in options_codes]:
        for i, c in enumerate(options_codes):
            if c.upper() == qc.upper():
                default_idx = i + 1
                break

    sel = st.selectbox(
        t["select_meeting"], [""] + options_codes, index=default_idx,
        format_func=lambda x: options_labels.get(x, f"— {t['enter_code']} —") if x else f"— {t['enter_code']} —",
        key="neg_sel"
    )
    mc = sel.strip().upper() if sel else ""
    if not mc:
        mc = st.text_input(t["meeting_code"], placeholder="AB12CD34", key="neg_manual").strip().upper()
    card_close()

    meeting = get_meeting(mc) if mc else None
    if not mc:
        st.info(t["enter_code"])
        st.stop()
    if not meeting:
        st.warning(t["not_found"])
        st.stop()
    if is_blocked(meeting):
        st.error(t["blocked"])
        st.stop()

    mtitle = meeting[1]
    vlink = meeting[3]

    card_open()
    st.success(f"📋 {mtitle}")
    st.markdown(f"{t['status']}: {sbadge(meeting[2])}", unsafe_allow_html=True)

    df = get_df(mc)
    if df.empty:
        empty(t["no_data"])
        card_close()
        st.stop()

    # Eşleşme durumunu göster
    matches = calc_matches(df, t["organizer"], t["participant"])

    if matches:
        st.markdown(f'<div class="section-head">✅ {t["matches"]} ({len(matches)})</div>', unsafe_allow_html=True)
        mdf = pd.DataFrame(matches)
        st.dataframe(mdf, use_container_width=True, hide_index=True)
        st.success("✅ Matching slots exist! Go to **Confirm & Calendar** to finalize.")
    else:
        # ══ EŞLEŞME YOK — MÜZAKEREYİ BAŞLAT ══
        st.warning(t["no_match"])
        st.markdown(t["no_match_help"])

        # Yakın eşleşmeler
        divider()
        near = calc_near_misses(df, t["organizer"], t["participant"])
        if near:
            st.markdown(f'<div class="section-head">{t["near_misses"]}</div>', unsafe_allow_html=True)
            for n in near[:5]:
                gap_text = f"⏱️ {n['Gap_Min']} min gap" if n['Gap_Min'] < 999 else ""
                st.markdown(
                    f"""<div class="proposal-card">
                    📅 <strong>{n['Date']}</strong><br>
                    👤 {n['Org_Name']}: {n['Org_Start']}–{n['Org_End']}<br>
                    👤 {n['Part_Name']}: {n['Part_Start']}–{n['Part_End']}<br>
                    {gap_text}</div>""",
                    unsafe_allow_html=True
                )

        # AI Önerileri
        divider()
        st.markdown(f'<div class="section-head">{t["ai_suggest"]}</div>', unsafe_allow_html=True)

        if st.button(t["ai_suggest_btn"], key="neg_ai_btn", use_container_width=True):
            with st.spinner(t["generating"]):
                try:
                    org_slots = get_slots_for_ai(df, t["organizer"])
                    part_slots = get_slots_for_ai(df, t["participant"])
                    suggestions = suggest_alternative_dates(org_slots, part_slots, mtitle, lang)
                    st.session_state["neg_suggestions"] = suggestions
                except Exception as e:
                    st.error(f"Error: {e}")

        if "neg_suggestions" in st.session_state and st.session_state["neg_suggestions"]:
            st.markdown(
                f'<div class="suggestion-box"><div class="suggestion-title">🤖 AI Suggestions</div>'
                f'{st.session_state["neg_suggestions"]}</div>',
                unsafe_allow_html=True
            )

    # ══ TARİH TEKLİFİ OLUŞTUR ══
    divider()
    st.markdown(f'<div class="section-head">{t["propose_new"]}</div>', unsafe_allow_html=True)
    st.caption(t["propose_hint"])

    pc1, pc2 = st.columns(2)
    with pc1:
        prop_name = st.text_input(t["name"], key="prop_name")
        prop_email = st.text_input(t["email"], key="prop_email")
        prop_role = st.selectbox(t["role"], [t["participant"], t["organizer"]], key="prop_role")
    with pc2:
        prop_date = st.date_input(t["propose_date"], key="prop_date")
        psc1, psc2 = st.columns(2)
        with psc1:
            prop_start = st.time_input(t["propose_start"], key="prop_start")
        with psc2:
            prop_end = st.time_input(t["propose_end"], key="prop_end")

    if st.button(t["propose_button"], use_container_width=True, key="prop_send"):
        if not prop_name:
            st.warning(t["enter_name"])
        elif prop_start >= prop_end:
            st.warning(t["time_error"])
        else:
            create_proposal(mc, prop_name, prop_email, prop_role, prop_date, prop_start, prop_end)
            st.success(t["proposal_sent"])
            st.rerun()

    # ══ MEVCUT TEKLİFLER ══
    divider()
    proposals = get_proposals(mc)
    if proposals:
        st.markdown(f'<div class="section-head">{t["proposals"]} ({len(proposals)})</div>', unsafe_allow_html=True)

        for prop in proposals:
            pid, pname, pemail, prole, pdate, pstart, pend, pstatus, pnote, presp, pcreated = prop
            card_cls = ""
            if pstatus == "accepted":
                card_cls = " proposal-accepted"
            elif pstatus == "rejected":
                card_cls = " proposal-rejected"

            st.markdown(
                f'<div class="proposal-card{card_cls}">'
                f'<strong>📨 {pname}</strong> ({prole}) — {sbadge(pstatus)}<br>'
                f'📅 {pdate} | ⏰ {pstart}–{pend}<br>'
                f'<small style="color:#94a3b8">{pcreated}</small>'
                f'{"<br>📝 " + pnote if pnote else ""}'
                f'</div>',
                unsafe_allow_html=True
            )

            # Bekleyen teklifler için işlem butonları
            if pstatus == "pending":
                bcol1, bcol2, bcol3 = st.columns(3)
                resp_note = st.text_input(t["response_note"], key=f"resp_note_{pid}", placeholder="Optional note")

                with bcol1:
                    if st.button(t["accept"], key=f"acc_{pid}", use_container_width=True):
                        update_proposal(pid, "accepted", resp_note, "admin")
                        st.success(t["proposal_accepted"])
                        st.rerun()

                with bcol2:
                    if st.button(t["confirm_from_proposal"], key=f"conf_prop_{pid}", use_container_width=True):
                        update_proposal(pid, "accepted", resp_note, "admin")
                        confirm_meeting_slot(mc, pdate, pstart, pend)
                        # Organizatörün uygunluğunu da ekle
                        add_availability(mc, "Organizer (from proposal)", "", t["organizer"], pdate, pstart, pend)
                        st.success(t["confirmed"])
                        st.rerun()

                with bcol3:
                    if st.button(t["reject"], key=f"rej_{pid}", use_container_width=True):
                        update_proposal(pid, "rejected", resp_note, "admin")
                        st.warning(t["proposal_rejected"])
                        st.rerun()
    else:
        empty(t["no_proposals"])

    # ══ ERTELE / YENİDEN PLANLA ══
    divider()
    st.markdown(f'<div class="section-head">⏸️ {t["postpone"]} / {t["reschedule"]}</div>', unsafe_allow_html=True)

    pcol1, pcol2 = st.columns(2)
    with pcol1:
        pp_reason = st.text_input(t["postpone_reason"], key="pp_reason", placeholder="Need more participants")
        if st.button(t["postpone"], use_container_width=True, key="pp_btn"):
            if meeting[2] == "confirmed":
                postpone_meeting(mc, pp_reason)
                st.warning(t["postponed"])
                st.rerun()
            else:
                st.info("Meeting is not confirmed yet. Add more availability slots instead.")

    with pcol2:
        st.caption("Reschedule clears all availability and resets the meeting.")
        if st.button(t["reschedule"], use_container_width=True, key="resc_btn"):
            postpone_meeting(mc, "Rescheduled — collecting new availability")
            st.warning(t["postponed"])
            st.rerun()

    card_close()


# ═══════════════════════════════════════════════════════
# 4. CONFIRM & CALENDAR
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
        for i, c in enumerate(options_codes):
            if c.upper() == qc.upper():
                default_idx = i + 1
                break

    sel = st.selectbox(
        t["select_meeting"], [""] + options_codes, index=default_idx,
        format_func=lambda x: options_labels.get(x, f"— {t['enter_code']} —") if x else f"— {t['enter_code']} —",
        key="conf_sel"
    )
    mc = sel.strip().upper() if sel else ""
    if not mc:
        mc = st.text_input(t["meeting_code"], placeholder="AB12CD34", key="conf_manual").strip().upper()
    card_close()

    meeting = get_meeting(mc) if mc else None
    if not mc:
        st.info(t["enter_code"])
        st.stop()
    if not meeting:
        st.warning(t["not_found"])
        st.stop()
    if is_blocked(meeting):
        st.error(t["blocked"])
        st.stop()

    mtitle, mstatus, vlink = meeting[1], meeting[2], meeting[3]

    card_open()
    st.success(f"📋 {mtitle}")
    st.markdown(f"{t['status']}: {sbadge(mstatus)}", unsafe_allow_html=True)

    # Video link
    st.markdown(f"### {t['video_link']}")
    if vlink:
        st.markdown(f'<div class="link-box">🎥 <a href="{vlink}" target="_blank">{vlink}</a></div>', unsafe_allow_html=True)
    else:
        st.info(t["no_video_link"])
    nvl = st.text_input(t["meeting_video_link"], value=vlink or "", key="upd_vl", placeholder=t["meeting_video_placeholder"])
    if st.button(t["update_link"], key="btn_upd"):
        update_meeting_link(mc, nvl)
        st.success(t["link_updated"])
        st.rerun()

    # Zaten onaylı
    if mstatus == "confirmed":
        divider()
        st.info(f"{t['already_confirmed']}: {meeting[4]} | {meeting[5]}-{meeting[6]}")
        ics = make_ics(mtitle, meeting[4], meeting[5], meeting[6], f"MeetAlign: {mc}", vlink)
        st.download_button(
            t["download_ics"], data=ics, file_name=f"meetalign_{mc}.ics",
            mime="text/calendar", use_container_width=True
        )

        # Onay e-postası
        divider()
        st.markdown(f'<div class="section-head">✉️ {t["generate_confirm_email"]}</div>', unsafe_allow_html=True)
        re = st.text_input(t["recipient_email"], key="conf_re_confirmed")

        if st.button(t["generate_confirm_email"], key="gen_conf_confirmed"):
            with st.spinner(t["generating"]):
                try:
                    ab = generate_confirmation_email(
                        mtitle, meeting[4], meeting[5], meeting[6],
                        language=lang, meeting_link=vlink or ""
                    )
                    st.session_state["conf_body"] = ab
                except Exception as e:
                    st.error(f"Error: {e}")

        ebody = st.text_area(
            "Email Preview",
            value=st.session_state.get(
                "conf_body",
                f"Meeting: {mtitle}\nDate: {meeting[4]}\nTime: {meeting[5]}-{meeting[6]}"
            ),
            height=220, key="conf_ta_confirmed"
        )

        if st.button(t["send_email"], use_container_width=True, key="btn_send_confirmed"):
            if not re:
                st.warning(t["recipient_email"])
            else:
                ok, msg = send_resend(re, f"Confirmed: {mtitle}", ebody)
                if ok:
                    st.success(t["email_sent"])
                else:
                    st.error(f"{t['email_failed']} {msg}")

        card_close()
        st.stop()

    # Onaylanmamış — uygunlukları göster
    df = get_df(mc)
    if df.empty:
        empty(t["no_data"])
        card_close()
        st.stop()

    divider()
    st.subheader(t["all_availability"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    matches = calc_matches(df, t["organizer"], t["participant"])
    st.subheader(t["matches"])

    if not matches:
        st.warning(t["no_match"])
        st.markdown(f"💡 Go to **{t['negotiate']}** page to get AI suggestions or propose new dates.")
        card_close()
        st.stop()

    metrics_html([
        (len(df), t["entries"]),
        (len(matches), t["match_count"]),
        (df["Email"].nunique(), t["people"])
    ])
    mdf = pd.DataFrame(matches)
    st.dataframe(mdf, use_container_width=True, hide_index=True)

    # AI Davet E-postası
    divider()
    st.markdown(f'<div class="section-head">{t["generate_invite"]}</div>', unsafe_allow_html=True)
    if st.button(t["generate_invite"], key="gen_inv"):
        with st.spinner(t["generating"]):
            try:
                ie = generate_meeting_email(mtitle, matches, language=lang, meeting_link=vlink or "")
                st.session_state["inv_email"] = ie
            except Exception as e:
                st.error(f"Error: {e}")

    if "inv_email" in st.session_state and st.session_state["inv_email"]:
        st.subheader(t["generated_email"])
        st.text_area("", value=st.session_state["inv_email"], height=280, key="inv_ta")

    # Slot seçimi ve onay
    divider()
    si = st.selectbox(
        t["select_slot"], range(len(matches)),
        format_func=lambda i: f"📅 {matches[i]['Date']} | ⏰ {matches[i]['Start']}-{matches[i]['End']} ({matches[i]['Organizer']} ↔ {matches[i]['Participant']})"
    )
    sel_m = matches[si]
    st.markdown(f"### ✅ **{sel_m['Date']}** | **{sel_m['Start']}** – **{sel_m['End']}**")
    st.markdown(f"👤 {sel_m['Organizer']} ↔ {sel_m['Participant']}")

    if st.button(t["confirm_meeting"], use_container_width=True, key="btn_confirm"):
        confirm_meeting_slot(mc, sel_m["Date"], sel_m["Start"], sel_m["End"])
        st.success(t["confirmed"])
        st.balloons()
        ics = make_ics(mtitle, sel_m["Date"], sel_m["Start"], sel_m["End"], f"MeetAlign: {mc}", vlink)
        st.download_button(
            t["download_ics"], data=ics, file_name=f"meetalign_{mc}.ics",
            mime="text/calendar", use_container_width=True
        )

    # Onay e-postası
    divider()
    st.markdown(f'<div class="section-head">✉️ {t["generate_confirm_email"]}</div>', unsafe_allow_html=True)
    re = st.text_input(t["recipient_email"], value=sel_m.get("Participant Email", ""), key="conf_re")

    if st.button(t["generate_confirm_email"], key="gen_conf"):
        with st.spinner(t["generating"]):
            try:
                ab = generate_confirmation_email(
                    mtitle, sel_m["Date"], sel_m["Start"], sel_m["End"],
                    language=lang, meeting_link=vlink or ""
                )
                st.session_state["conf_body"] = ab
            except Exception as e:
                st.error(f"Error: {e}")

    ebody = st.text_area(
        "Email Preview",
        value=st.session_state.get(
            "conf_body",
            f"Meeting: {mtitle}\nDate: {sel_m['Date']}\nTime: {sel_m['Start']}-{sel_m['End']}\n\nClick 'Generate' above for AI email."
        ),
        height=220, key="conf_ta"
    )

    if st.button(t["send_email"], use_container_width=True, key="btn_send"):
        if not re:
            st.warning(t["recipient_email"])
        else:
            ok, msg = send_resend(re, f"Confirmed: {mtitle}", ebody)
            if ok:
                st.success(t["email_sent"])
            else:
                st.error(f"{t['email_failed']} {msg}")
    card_close()


# ═══════════════════════════════════════════════════════
# 5. AI CHATBOT
# ═══════════════════════════════════════════════════════
elif menu == t["chatbot"]:
    st.header(f"🤖 {t['chatbot']}")
    guide(t["chat_help"])

    card_open()
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    mode = st.radio(t["chat_mode"], [t["mode_command"], t["mode_chat"]], horizontal=True)

    # Chat geçmişi
    for ch in st.session_state["chat_history"]:
        icon = "🧑" if ch["role"] == "user" else "🤖"
        if ch["role"] == "user":
            st.markdown(f"**{icon} You:** {ch['text']}")
        else:
            st.markdown(f"**{icon} AI:** {ch['text']}")
        st.markdown("---")

    um = st.text_area(t["chat_input"], height=120, placeholder=t["chat_help"], key="chat_ta")

    if st.button(t["chat_button"], use_container_width=True, key="chat_btn"):
        if not um:
            st.warning(t["chat_input"])
        else:
            st.session_state["chat_history"].append({"role": "user", "text": um})

            if mode == t["mode_chat"]:
                with st.spinner("..."):
                    reply = ai_chatbot_response(um, language=lang)
                st.session_state["chat_history"].append({"role": "ai", "text": reply})
                st.rerun()
            else:
                with st.spinner("..."):
                    parsed, err = parse_meeting_command(um)
                if err:
                    st.error(err)
                    st.session_state["chat_history"].append({"role": "ai", "text": f"Error: {err}"})
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
                            etv = (datetime.strptime(stv, "%H:%M") + timedelta(minutes=30)).strftime("%H:%M")
                        except:
                            etv = ""
                    mc2 = create_meeting(mt2)
                    ml2 = f"{base_url()}?meeting={mc2}"
                    st.success(t["created"])
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.text_input(t["meeting_code"], value=mc2, key="ch_mc", disabled=True)
                    with c2:
                        st.text_input(t["meeting_link"], value=ml2, key="ch_ml", disabled=True)
                    if dv and stv and etv:
                        add_availability(
                            mc2, "Organizer", "", t["organizer"], dv,
                            f"{stv}:00" if len(stv) == 5 else stv,
                            f"{etv}:00" if len(etv) == 5 else etv
                        )
                        st.info("✅ Organizer availability added.")
                    st.subheader(t["copy_invitation"])
                    st.code(f"Hello {pn},\n\nMeeting: {mt2}\nLink: {ml2}\nCode: {mc2}\n\nBest regards")
                    st.session_state["chat_history"].append(
                        {"role": "ai", "text": f"Created: {mt2} | {mc2}"}
                    )

    # Clear chat
    if st.session_state["chat_history"]:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state["chat_history"] = []
            st.rerun()
    card_close()


# ═══════════════════════════════════════════════════════
# 6. MANAGE MEETINGS (ADMIN)
# ═══════════════════════════════════════════════════════
elif menu == t["manage"]:
    st.header(f"⚙️ {t['manage']}")

    if not check_admin():
        card_open()
        st.markdown('<div class="admin-box">🔐 <strong>Admin Authentication</strong></div>', unsafe_allow_html=True)
        apw = st.text_input(t["admin_password"], type="password", key="apw")
        if st.button(t["admin_login"], use_container_width=True, key="btn_adm"):
            if apw == ADMIN_PASSWORD:
                st.session_state["admin_auth"] = True
                st.rerun()
            else:
                st.error(t["admin_wrong"])
        card_close()
        st.markdown(f'<div class="admin-locked">{t["admin_locked"]}</div>', unsafe_allow_html=True)
        st.stop()

    st.markdown(f'<div class="admin-success">🔓 {t["admin_logged"]}</div>', unsafe_allow_html=True)
    guide("Select any meeting below to manage. Cancel, archive, restore, postpone or permanently delete.")

    all_m = all_meetings_for_manage()

    if not all_m:
        empty(t["no_meetings"])
        st.stop()

    # Dashboard istatistikleri
    stats = get_meeting_stats()
    metrics_html([
        (stats["total"], t["total"]),
        (stats["active"], t["active_meetings"]),
        (stats["confirmed"], t["confirmed_meetings"]),
        (stats["pending_proposals"], t["pending_proposals"]),
    ])

    # Tabs ile kategorili görünüm
    card_open()
    tabs = st.tabs([t["active_meetings"], t["confirmed_meetings"], t["archived_meetings"]])

    with tabs[0]:
        actives = get_active_meetings()
        if actives:
            for m in actives:
                st.markdown(mchtml(m[0], m[1], m[2], m[3]), unsafe_allow_html=True)
        else:
            empty(t["no_meetings"])

    with tabs[1]:
        confirmed = get_confirmed_meetings()
        if confirmed:
            for m in confirmed:
                st.markdown(mchtml(m[0], m[1], m[2], m[3]), unsafe_allow_html=True)
        else:
            empty(t["no_meetings"])

    with tabs[2]:
        archived = get_archived_meetings()
        if archived:
            for a in archived:
                reason = f" — <em>{a[4]}</em>" if a[4] else ""
                st.markdown(
                    f"""<div class="meeting-card" style="border-color:#fecaca">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                    <div><span class="meeting-card-title">{a[1]}</span>&nbsp;
                    <span class="meeting-card-code">{a[0]}</span>{reason}</div>
                    <div class="meeting-card-date">{a[3]}</div></div></div>""",
                    unsafe_allow_html=True
                )
        else:
            empty(t["no_meetings"])

    # Dropdown ile toplantı seç
    divider()
    labels = {m[0]: f"{m[1]} ({m[0]}) [{m[2]}]" for m in all_m}
    sel_code = st.selectbox(
        t["select_to_manage"],
        [m[0] for m in all_m],
        format_func=lambda x: labels.get(x, x),
        key="manage_sel"
    )
    card_close()

    # Seçilen toplantının detayları
    meeting = get_meeting(sel_code) if sel_code else None

    if meeting:
        card_open()
        st.markdown(f'<div class="section-head">📋 {t["meeting_details"]}</div>', unsafe_allow_html=True)
        st.markdown(f"### {meeting[1]}")
        st.markdown(f"**Code:** `{sel_code}` &nbsp;&nbsp; {t['status']}: {sbadge(meeting[2])}", unsafe_allow_html=True)

        if meeting[3]:
            st.markdown(f'<div class="link-box">🎥 <a href="{meeting[3]}" target="_blank">{meeting[3]}</a></div>', unsafe_allow_html=True)

        if meeting[2] == "confirmed" and meeting[4]:
            st.info(f"📅 Confirmed: {meeting[4]} | {meeting[5]}-{meeting[6]}")

        # Uygunluklar
        edf = get_df(sel_code)
        if not edf.empty:
            divider()
            st.markdown(f'<div class="section-head">📊 {t["all_availability"]}</div>', unsafe_allow_html=True)
            metrics_html([(len(edf), t["entries"]), (edf["Email"].nunique(), t["people"])])
            st.dataframe(edf, use_container_width=True, hide_index=True)

        # Teklifler
        proposals = get_proposals(sel_code)
        if proposals:
            divider()
            st.markdown(f'<div class="section-head">{t["proposals"]} ({len(proposals)})</div>', unsafe_allow_html=True)
            for prop in proposals:
                pid, pname, pemail, prole, pdate, pstart, pend, pstatus, pnote, presp, pcreated = prop
                card_cls = ""
                if pstatus == "accepted":
                    card_cls = " proposal-accepted"
                elif pstatus == "rejected":
                    card_cls = " proposal-rejected"
                st.markdown(
                    f'<div class="proposal-card{card_cls}">'
                    f'<strong>{pname}</strong> ({prole}) — {sbadge(pstatus)}<br>'
                    f'📅 {pdate} | ⏰ {pstart}–{pend}'
                    f'{"<br>📝 " + pnote if pnote else ""}'
                    f'</div>',
                    unsafe_allow_html=True
                )

                if pstatus == "pending":
                    resp_note = st.text_input(t["response_note"], key=f"mg_resp_{pid}")
                    acol1, acol2, acol3 = st.columns(3)
                    with acol1:
                        if st.button(t["accept"], key=f"mg_acc_{pid}", use_container_width=True):
                            update_proposal(pid, "accepted", resp_note, "admin")
                            st.success(t["proposal_accepted"])
                            st.rerun()
                    with acol2:
                        if st.button(t["confirm_from_proposal"], key=f"mg_cfp_{pid}", use_container_width=True):
                            update_proposal(pid, "accepted", resp_note, "admin")
                            confirm_meeting_slot(sel_code, pdate, pstart, pend)
                            st.success(t["confirmed"])
                            st.rerun()
                    with acol3:
                        if st.button(t["reject"], key=f"mg_rej_{pid}", use_container_width=True):
                            update_proposal(pid, "rejected", resp_note, "admin")
                            st.warning(t["proposal_rejected"])
                            st.rerun()

        # İşlemler
        divider()
        st.markdown(f'<div class="section-head">🔧 {t["actions"]}</div>', unsafe_allow_html=True)

        mstatus = meeting[2]
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if mstatus in ("active", "confirmed"):
                reason = st.text_input(t["cancel_reason"], key="mg_reason", placeholder="Optional reason")
                if st.button(t["cancel"], use_container_width=True, key="mg_cancel"):
                    cancel_meeting(sel_code, reason)
                    st.warning(t["cancelled"])
                    st.rerun()

        with col2:
            if mstatus in ("active", "confirmed"):
                if mstatus == "confirmed":
                    pp_reason = st.text_input(t["postpone_reason"], key="mg_pp_reason")
                    if st.button(t["postpone"], use_container_width=True, key="mg_postpone"):
                        postpone_meeting(sel_code, pp_reason)
                        st.warning(t["postponed"])
                        st.rerun()
                else:
                    if st.button(t["archive"], use_container_width=True, key="mg_archive"):
                        archive_meeting(sel_code)
                        st.info("Archived.")
                        st.rerun()

        with col3:
            if mstatus in ("cancelled", "archived"):
                if st.button(t["restore"], use_container_width=True, key="mg_restore"):
                    restore_meeting(sel_code)
                    st.success(t["restored"])
                    st.rerun()

        with col4:
            if mstatus in ("cancelled", "archived"):
                st.caption(t["delete_confirm"])
                if st.button(t["delete_permanent"], use_container_width=True, key="mg_del"):
                    delete_meeting_permanent(sel_code)
                    st.error(t["deleted"])
                    st.rerun()

        # Video link güncelle
        divider()
        st.markdown('<div class="section-head">🔗 Update Video Link</div>', unsafe_allow_html=True)
        new_vl = st.text_input(t["meeting_video_link"], value=meeting[3] or "", key="mg_vl")
        if st.button(t["update_link"], key="mg_upd"):
            update_meeting_link(sel_code, new_vl)
            st.success(t["link_updated"])
            st.rerun()

        # Geçmiş
        divider()
        st.markdown(f'<div class="section-head">{t["history"]}</div>', unsafe_allow_html=True)
        hist = get_meeting_history(sel_code)
        if hist:
            for h in hist:
                st.markdown(
                    f'<div class="history-item"><strong>{h[0]}</strong> — {h[1]}<br>'
                    f'<small style="color:#94a3b8">{h[2]}</small></div>',
                    unsafe_allow_html=True
                )
        else:
            empty(t["no_history"])
        card_close()
