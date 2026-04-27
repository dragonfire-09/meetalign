import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from database import (
    init_db, create_meeting, get_meeting, update_meeting_link,
    add_availability, get_availability, clear_availability,
    cancel_meeting, archive_meeting,
    restore_meeting, confirm_meeting_slot, delete_meeting_permanent,
    get_meeting_history, get_all_meetings, get_active_meetings,
    get_archived_meetings, get_confirmed_meetings, postpone_meeting,
    create_proposal, get_proposals, get_pending_proposals,
    get_all_pending_proposals, update_proposal, expire_other_proposals,
    get_meeting_stats
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
# CSS
# ═══════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    :root{
        --blue:#2563eb;--indigo:#4f46e5;--green:#16a34a;--red:#dc2626;
        --amber:#d97706;--gray:#6b7280;--purple:#7c3aed;--teal:#0d9488;
        --light:#f8fafc;--white:#ffffff
    }
    .stApp{background:linear-gradient(135deg,#f0f4ff 0%,#e8ecf8 50%,#f5f3ff 100%);font-family:'Inter',sans-serif}
    section[data-testid="stSidebar"]{background:linear-gradient(180deg,#fff 0%,#f8fafc 100%);border-right:1px solid #e2e8f0}

    .hero{background:linear-gradient(135deg,#fff 0%,#f0f4ff 100%);padding:32px 40px;border-radius:28px;
          border:1px solid #e2e8f0;box-shadow:0 25px 60px rgba(15,23,42,.06);margin-bottom:24px;position:relative;overflow:hidden}
    .hero::before{content:'';position:absolute;top:-50%;right:-20%;width:400px;height:400px;
                  background:radial-gradient(circle,rgba(37,99,235,.06) 0%,transparent 70%);border-radius:50%}
    .hero-title{font-size:44px;font-weight:900;color:#0f172a;margin-bottom:6px;letter-spacing:-1px;position:relative}
    .hero-sub{color:#64748b;font-size:16px;line-height:1.7;position:relative}
    .hero-steps{margin-top:12px;font-size:14px;font-weight:600;color:#334155;position:relative}

    .card{background:var(--white);padding:26px;border-radius:22px;border:1px solid #e2e8f0;
          box-shadow:0 10px 36px rgba(15,23,42,.04);margin:18px 0;transition:all .2s}
    .card:hover{box-shadow:0 14px 46px rgba(15,23,42,.06)}
    .guide{background:linear-gradient(135deg,#eff6ff 0%,#f0f4ff 100%);padding:16px 20px;border-radius:14px;
           border:1px solid #bfdbfe;color:#1e40af;margin-bottom:20px;font-size:14px;font-weight:500;line-height:1.6}
    .pill{display:inline-block;padding:5px 12px;background:#eff6ff;color:var(--blue);border-radius:999px;
          font-size:12px;font-weight:700;margin:3px 5px 3px 0;border:1px solid #bfdbfe;letter-spacing:.3px}
    .pill-green{background:#f0fdf4;color:var(--green);border-color:#bbf7d0}
    .pill-red{background:#fef2f2;color:var(--red);border-color:#fecaca}
    .pill-amber{background:#fffbeb;color:var(--amber);border-color:#fde68a}
    .pill-gray{background:#f9fafb;color:var(--gray);border-color:#e5e7eb}
    .pill-purple{background:#f5f3ff;color:var(--purple);border-color:#ddd6fe}
    .pill-teal{background:#f0fdfa;color:var(--teal);border-color:#99f6e4}

    .empty{background:linear-gradient(135deg,#fff 0%,#f8fafc 100%);padding:36px;border-radius:22px;
           border:2px dashed #cbd5e1;text-align:center;color:#94a3b8;margin-top:16px}
    .empty h3{font-size:36px;margin-bottom:8px}.empty p{font-size:14px}

    .metric-row{display:flex;gap:14px;margin:18px 0;flex-wrap:wrap}
    .metric-box{flex:1;min-width:110px;background:linear-gradient(135deg,#fff 0%,#f8fafc 100%);padding:20px;border-radius:18px;
                border:1px solid #e2e8f0;box-shadow:0 6px 20px rgba(15,23,42,.03);text-align:center;transition:all .2s}
    .metric-box:hover{transform:translateY(-2px);box-shadow:0 10px 28px rgba(15,23,42,.06)}
    .metric-num{font-size:30px;font-weight:900;color:var(--blue)}
    .metric-lbl{font-size:12px;color:var(--gray);margin-top:4px;font-weight:600}

    .history-item{padding:11px 15px;border-left:4px solid var(--blue);margin-bottom:9px;
                  background:linear-gradient(90deg,#f0f4ff 0%,#fff 100%);border-radius:0 12px 12px 0;font-size:13px}
    .meeting-card{padding:16px 20px;border-radius:16px;border:1px solid #e2e8f0;margin-bottom:10px;
                  background:linear-gradient(135deg,#fff 0%,#fafbff 100%);transition:all .15s}
    .meeting-card:hover{border-color:#93c5fd;box-shadow:0 5px 18px rgba(37,99,235,.08);transform:translateY(-1px)}
    .meeting-card-title{font-weight:700;font-size:15px;color:#1e293b}
    .meeting-card-code{font-family:monospace;background:#f1f5f9;padding:3px 10px;border-radius:8px;
                       font-size:13px;color:#475569;font-weight:600}
    .meeting-card-date{font-size:12px;color:#94a3b8;margin-top:4px}

    .status-active{color:var(--green);font-weight:700}.status-confirmed{color:var(--blue);font-weight:700}
    .status-cancelled{color:var(--red);font-weight:700}.status-archived{color:var(--gray);font-weight:700}
    .status-pending{color:var(--amber);font-weight:700}.status-expired{color:var(--gray);font-weight:600}

    .proposal-card{padding:15px 18px;border-radius:14px;border:1.5px solid #fde68a;margin-bottom:10px;
                   background:linear-gradient(135deg,#fffbeb 0%,#fef3c7 100%);transition:all .15s}
    .proposal-card:hover{box-shadow:0 5px 18px rgba(217,119,6,.1)}
    .proposal-accepted{border-color:#86efac !important;background:linear-gradient(135deg,#f0fdf4 0%,#dcfce7 100%) !important}
    .proposal-rejected{border-color:#fca5a5 !important;background:linear-gradient(135deg,#fef2f2 0%,#fee2e2 100%) !important}
    .proposal-expired{border-color:#e5e7eb !important;background:linear-gradient(135deg,#f9fafb 0%,#f3f4f6 100%) !important;opacity:.7}
    .proposal-counter{border-color:#ddd6fe !important;background:linear-gradient(135deg,#f5f3ff 0%,#ede9fe 100%) !important}

    .suggestion-box{background:linear-gradient(135deg,#f5f3ff 0%,#ede9fe 100%);border:1.5px solid #ddd6fe;
                    border-radius:16px;padding:20px;margin:14px 0;white-space:pre-line}
    .suggestion-title{font-size:15px;font-weight:700;color:var(--purple);margin-bottom:10px}

    .near-miss-card{padding:14px 18px;border-radius:14px;border:1.5px solid #fed7aa;margin-bottom:8px;
                    background:linear-gradient(135deg,#fff7ed 0%,#ffedd5 100%)}
    .match-card{padding:14px 18px;border-radius:14px;border:1.5px solid #86efac;margin-bottom:8px;
                background:linear-gradient(135deg,#f0fdf4 0%,#dcfce7 100%)}

    .action-hint{background:#fffbeb;border:1px solid #fde68a;border-radius:12px;padding:12px 16px;
                 font-size:13px;color:#92400e;margin:8px 0;font-weight:500}
    .confirmed-banner{background:linear-gradient(135deg,#ecfdf5 0%,#d1fae5 100%);border:2px solid #6ee7b7;
                      border-radius:18px;padding:20px 24px;margin:12px 0;text-align:center}
    .confirmed-banner h3{font-size:20px;font-weight:800;color:#065f46;margin:0}
    .confirmed-banner p{font-size:15px;color:#047857;margin:6px 0 0}

    .timeline-dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:8px}
    .dot-pending{background:var(--amber)}.dot-accepted{background:var(--green)}
    .dot-rejected{background:var(--red)}.dot-expired{background:var(--gray)}

    .tab-badge{background:var(--red);color:#fff;border-radius:50%;padding:2px 7px;
               font-size:10px;font-weight:800;margin-left:5px;vertical-align:middle}

    .link-box{background:linear-gradient(135deg,#f0fdf4 0%,#ecfdf5 100%);border:1px solid #86efac;
              border-radius:12px;padding:13px 16px;margin:10px 0;font-size:14px;word-break:break-all}
    .link-box a{color:var(--blue);text-decoration:none;font-weight:600}
    .section-head{font-size:17px;font-weight:800;color:#1e293b;margin-bottom:12px;padding-bottom:8px;border-bottom:2px solid #e2e8f0}
    .divider{height:1px;background:linear-gradient(90deg,transparent,#e2e8f0,transparent);margin:22px 0}

    .admin-box{background:linear-gradient(135deg,#fffbeb 0%,#fef3c7 100%);border:1px solid #fcd34d;
               border-radius:16px;padding:22px;margin:14px 0;text-align:center}
    .admin-locked{background:linear-gradient(135deg,#fef2f2 0%,#fee2e2 100%);border:1px solid #fca5a5;
                  border-radius:16px;padding:26px;text-align:center;color:var(--red);margin:14px 0;font-weight:600}
    .admin-success{background:linear-gradient(135deg,#f0fdf4 0%,#dcfce7 100%);border:1px solid #86efac;
                   border-radius:12px;padding:12px 18px;color:var(--green);font-weight:700;text-align:center;margin-bottom:14px}

    div.stButton>button{
        background:linear-gradient(135deg,var(--blue) 0%,var(--indigo) 100%);color:#fff;
        border:none;border-radius:12px;padding:.75rem 1.3rem;font-weight:700;
        box-shadow:0 8px 24px rgba(37,99,235,.22);transition:all .2s;font-size:14px
    }
    div.stButton>button:hover{
        background:linear-gradient(135deg,#1d4ed8 0%,#4338ca 100%);
        color:#fff;border:none;transform:translateY(-2px);box-shadow:0 12px 32px rgba(37,99,235,.28)
    }
    div.stButton>button[kind="secondary"]{
        background:linear-gradient(135deg,#f8fafc 0%,#f1f5f9 100%);
        color:#475569;border:1.5px solid #e2e8f0;
        box-shadow:0 2px 8px rgba(15,23,42,.06)
    }
    div.stButton>button[kind="secondary"]:hover{
        background:linear-gradient(135deg,#e2e8f0 0%,#cbd5e1 100%);
        color:#1e293b;border:1.5px solid #cbd5e1
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# TEXTS
# ═══════════════════════════════════════════════════════
TEXT = {
    "English": {
        "menu": "Workspace", "dashboard": "Dashboard", "create": "Create Meeting",
        "availability": "Add Availability", "negotiate": "Negotiate & Propose",
        "confirm": "Confirm & Calendar", "chatbot": "AI Chatbot", "manage": "Manage Meetings",
        "title": "MeetAlign",
        "subtitle": "Smart meeting scheduler for project teams, researchers and consortium partners.",
        "hero": "Create → Collect availability → Negotiate → Confirm → Send invite",
        "meeting_title": "Meeting Title", "meeting_placeholder": "EIC Pathfinder Meeting",
        "meeting_video_link": "Zoom / Google Meet Link (optional)",
        "meeting_video_placeholder": "https://zoom.us/j/... or https://meet.google.com/...",
        "create_button": "🚀 Create Meeting", "meeting_code": "Meeting Code",
        "meeting_link": "Meeting Link", "copy_invitation": "📋 Copy invitation",
        "created": "✅ Meeting created!",
        "org_name": "Organizer Name", "org_email": "Organizer Email",
        "org_date": "Available Date", "org_start": "Start", "org_end": "End",
        "org_info": "👤 Organizer Availability (auto-added)",
        "name": "Your Name", "email": "Your Email", "role": "Role",
        "organizer": "Organizer", "participant": "Participant",
        "date": "Date", "start": "Start Time", "end": "End Time",
        "save": "💾 Save Availability", "saved": "✅ Saved!",
        "not_found": "Meeting not found.", "enter_code": "Select or enter code.",
        "enter_name": "Enter your name.", "time_error": "End must be after start.",
        "blocked": "🚫 Meeting not active.", "select_meeting": "Select a meeting",
        "existing_meetings": "📋 Your Meetings",
        "all_availability": "All Availability", "matches": "Matching Slots",
        "no_data": "No availability yet.", "no_match": "No matching slots found.",
        "select_slot": "Select slot", "confirm_meeting": "✅ Confirm This Slot",
        "confirmed": "Confirmed!", "already_confirmed": "Already confirmed",
        "download_ics": "📥 Download .ics", "video_link": "🔗 Video Link",
        "no_video_link": "No video link set.", "update_link": "Update",
        "link_updated": "Updated!",
        "send_email": "📧 Send Email", "recipient_email": "Recipient Email",
        "email_sent": "✅ Sent!", "email_failed": "❌ Failed.",
        "generate_invite": "🤖 Generate AI Email", "generated_email": "Generated Email",
        "generate_confirm_email": "🤖 Generate Confirmation Email",
        "chat_help": "Example: Plan a meeting with Moshira on 2026-05-12 at 14:00.",
        "chat_input": "Type your message...", "chat_button": "Send", "parsed": "AI understood:",
        "chat_mode": "Mode", "mode_command": "Create Meeting", "mode_chat": "Free Chat",
        "admin_password": "🔑 Password", "admin_login": "Login",
        "admin_wrong": "Wrong password.", "admin_locked": "🔒 Admin login required.",
        "admin_logged": "🔓 Admin access granted.",
        "cancel": "🚫 Cancel", "cancel_reason": "Reason", "cancelled": "Cancelled.",
        "archive": "📦 Archive", "restore": "♻️ Restore", "restored": "Restored.",
        "delete_permanent": "🗑️ Delete Forever", "deleted": "Deleted.",
        "delete_confirm": "⚠️ Cannot be undone!",
        "active_meetings": "🟢 Active", "confirmed_meetings": "🔵 Confirmed",
        "archived_meetings": "📦 Archived / Cancelled", "no_meetings": "No meetings.",
        "history": "📜 History", "no_history": "No history.",
        "status": "Status", "entries": "Entries", "match_count": "Matches", "people": "People",
        "select_to_manage": "Select a meeting to manage", "actions": "Actions",
        "meeting_details": "Meeting Details", "generating": "Generating...",
        "propose_new": "📨 Propose New Date",
        "propose_hint": "No overlap? Suggest a time that works for you.",
        "proposals": "📨 Proposals", "pending": "Pending", "accepted": "Accepted",
        "rejected": "Rejected", "expired": "Expired",
        "accept": "✅ Accept", "reject": "❌ Reject",
        "counter": "🔄 Counter-Propose",
        "no_proposals": "No proposals yet.",
        "ai_suggest": "🤖 AI Suggestions", "ai_suggest_btn": "🤖 Get AI Suggestions",
        "near_misses": "🎯 Near Misses (< 120 min gap)",
        "postpone": "⏸️ Postpone", "postpone_reason": "Reason for postponement",
        "postponed": "Meeting postponed. Collecting new availability.",
        "reschedule": "🔄 Reschedule (clear availability)",
        "total": "Total", "pending_proposals": "Pending Proposals",
        "response_note": "Response note (optional)", "propose_button": "📨 Send Proposal",
        "proposal_sent": "✅ Proposal sent!", "proposal_accepted": "✅ Proposal accepted!",
        "proposal_rejected": "❌ Proposal rejected.",
        "propose_date": "Proposed Date", "propose_start": "Proposed Start",
        "propose_end": "Proposed End",
        "confirm_from_proposal": "✅ Accept & Confirm",
        "no_match_help": (
            "💡 No overlapping times found. Options:\n"
            "1. Get AI suggestions (Tab 2)\n"
            "2. Propose a new time (Tab 3)\n"
            "3. Add more availability slots"
        ),
        "tab_status": "📊 Status",
        "tab_ai": "🤖 AI & Near Misses",
        "tab_propose": "📨 Propose",
        "tab_proposals": "📋 All Proposals",
        "tab_postpone": "⏸️ Postpone",
        "go_confirm": "➡️ Go to Confirm & Calendar",
        "shift_suggest": "Try shifting by",
        "minutes": "minutes",
        "counter_propose": "🔄 Submit Counter-Proposal",
        "counter_hint": "Propose a different time back:",
        "clear_avail": "🗑️ Clear Availability (reset slots)",
        "avail_cleared": "✅ Availability cleared.",
        "avail_warning": "This will delete ALL availability entries for this meeting.",
    },
    "Türkçe": {
        "menu": "Çalışma Alanı", "dashboard": "Gösterge Paneli",
        "create": "Toplantı Oluştur", "availability": "Uygunluk Ekle",
        "negotiate": "Müzakere & Teklif",
        "confirm": "Onayla & Takvim", "chatbot": "AI Chatbot",
        "manage": "Toplantı Yönetimi",
        "title": "MeetAlign",
        "subtitle": "Proje ekipleri ve araştırmacılar için akıllı toplantı planlayıcı.",
        "hero": "Oluştur → Uygunluk topla → Müzakere → Onayla → Davet gönder",
        "meeting_title": "Toplantı Başlığı",
        "meeting_placeholder": "EIC Pathfinder Toplantısı",
        "meeting_video_link": "Zoom / Google Meet Linki (opsiyonel)",
        "meeting_video_placeholder": "https://zoom.us/j/... veya https://meet.google.com/...",
        "create_button": "🚀 Oluştur", "meeting_code": "Toplantı Kodu",
        "meeting_link": "Toplantı Linki", "copy_invitation": "📋 Daveti kopyala",
        "created": "✅ Oluşturuldu!",
        "org_name": "Organizatör Adı", "org_email": "Organizatör E-posta",
        "org_date": "Uygun Tarih", "org_start": "Başlangıç", "org_end": "Bitiş",
        "org_info": "👤 Organizatör Uygunluğu (otomatik eklenir)",
        "name": "Adınız", "email": "E-posta", "role": "Rol",
        "organizer": "Organizatör", "participant": "Katılımcı",
        "date": "Tarih", "start": "Başlangıç", "end": "Bitiş",
        "save": "💾 Kaydet", "saved": "✅ Kaydedildi!",
        "not_found": "Bulunamadı.", "enter_code": "Seçin veya kod girin.",
        "enter_name": "Adınızı girin.", "time_error": "Bitiş başlangıçtan sonra olmalı.",
        "blocked": "🚫 Toplantı aktif değil.", "select_meeting": "Toplantı seçin",
        "existing_meetings": "📋 Toplantılar",
        "all_availability": "Tüm Uygunluklar", "matches": "Ortak Saatler",
        "no_data": "Henüz uygunluk yok.", "no_match": "Eşleşen zaman dilimi bulunamadı.",
        "select_slot": "Saat seçin", "confirm_meeting": "✅ Bu Saati Onayla",
        "confirmed": "Onaylandı!", "already_confirmed": "Zaten onaylı",
        "download_ics": "📥 .ics İndir", "video_link": "🔗 Video Linki",
        "no_video_link": "Video linki yok.", "update_link": "Güncelle",
        "link_updated": "Güncellendi!",
        "send_email": "📧 Gönder", "recipient_email": "Alıcı E-posta",
        "email_sent": "✅ Gönderildi!", "email_failed": "❌ Gönderilemedi.",
        "generate_invite": "🤖 AI Davet Oluştur", "generated_email": "Oluşturulan E-posta",
        "generate_confirm_email": "🤖 AI Onay E-postası",
        "chat_help": "Örnek: 12 Mayıs 2026 14:00'te Moshira ile toplantı planla.",
        "chat_input": "Mesajınızı yazın...", "chat_button": "Gönder",
        "parsed": "AI anladı:", "chat_mode": "Mod",
        "mode_command": "Toplantı Oluştur", "mode_chat": "Serbest Sohbet",
        "admin_password": "🔑 Şifre", "admin_login": "Giriş",
        "admin_wrong": "Yanlış şifre.", "admin_locked": "🔒 Admin girişi gerekli.",
        "admin_logged": "🔓 Erişim sağlandı.",
        "cancel": "🚫 İptal", "cancel_reason": "Neden", "cancelled": "İptal edildi.",
        "archive": "📦 Arşivle", "restore": "♻️ Geri Al", "restored": "Geri alındı.",
        "delete_permanent": "🗑️ Kalıcı Sil", "deleted": "Silindi.",
        "delete_confirm": "⚠️ Geri alınamaz!",
        "active_meetings": "🟢 Aktif", "confirmed_meetings": "🔵 Onaylı",
        "archived_meetings": "📦 Arşiv / İptal", "no_meetings": "Toplantı yok.",
        "history": "📜 Geçmiş", "no_history": "Geçmiş yok.",
        "status": "Durum", "entries": "Kayıt", "match_count": "Eşleşme", "people": "Kişi",
        "select_to_manage": "Yönetilecek toplantıyı seçin", "actions": "İşlemler",
        "meeting_details": "Toplantı Detayları", "generating": "Oluşturuluyor...",
        "propose_new": "📨 Yeni Tarih Öner",
        "propose_hint": "Örtüşme yok mu? Size uygun bir zaman önerin.",
        "proposals": "📨 Teklifler", "pending": "Bekliyor", "accepted": "Kabul Edildi",
        "rejected": "Reddedildi", "expired": "Süresi Doldu",
        "accept": "✅ Kabul Et", "reject": "❌ Reddet",
        "counter": "🔄 Karşı Teklif",
        "no_proposals": "Henüz teklif yok.",
        "ai_suggest": "🤖 AI Önerileri", "ai_suggest_btn": "🤖 AI Önerisi Al",
        "near_misses": "🎯 Yakın Eşleşmeler (< 120 dk fark)",
        "postpone": "⏸️ Ertele", "postpone_reason": "Erteleme nedeni",
        "postponed": "Toplantı ertelendi. Yeni uygunluklar toplanıyor.",
        "reschedule": "🔄 Yeniden Planla (uygunlukları sıfırla)",
        "total": "Toplam", "pending_proposals": "Bekleyen Teklifler",
        "response_note": "Yanıt notu (opsiyonel)", "propose_button": "📨 Teklif Gönder",
        "proposal_sent": "✅ Teklif gönderildi!",
        "proposal_accepted": "✅ Teklif kabul edildi!",
        "proposal_rejected": "❌ Teklif reddedildi.",
        "propose_date": "Önerilen Tarih", "propose_start": "Önerilen Başlangıç",
        "propose_end": "Önerilen Bitiş",
        "confirm_from_proposal": "✅ Kabul Et & Onayla",
        "no_match_help": (
            "💡 Örtüşen zaman bulunamadı. Seçenekler:\n"
            "1. AI önerisi alın (Sekme 2)\n"
            "2. Yeni zaman teklif edin (Sekme 3)\n"
            "3. Daha fazla uygunluk ekleyin"
        ),
        "tab_status": "📊 Durum",
        "tab_ai": "🤖 AI & Yakın Eşleşmeler",
        "tab_propose": "📨 Teklif Et",
        "tab_proposals": "📋 Tüm Teklifler",
        "tab_postpone": "⏸️ Ertele",
        "go_confirm": "➡️ Onayla & Takvim'e Git",
        "shift_suggest": "Kaydırma önerisi:",
        "minutes": "dakika",
        "counter_propose": "🔄 Karşı Teklif Gönder",
        "counter_hint": "Farklı bir zaman önerin:",
        "clear_avail": "🗑️ Uygunlukları Temizle",
        "avail_cleared": "✅ Uygunluklar temizlendi.",
        "avail_warning": "Bu toplantının TÜM uygunluk kayıtları silinecek.",
    }
}


# ═══════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════
def base_url():
    try:
        return st.context.url.split("?")[0]
    except Exception:
        return "https://your-app.streamlit.app"


def q_code():
    try:
        return st.query_params.get("meeting", "")
    except Exception:
        return ""


def card_open():
    st.markdown('<div class="card">', unsafe_allow_html=True)


def card_close():
    st.markdown('</div>', unsafe_allow_html=True)


def guide(txt):
    st.markdown('<div class="guide">{}</div>'.format(txt), unsafe_allow_html=True)


def empty_state(msg):
    st.markdown('<div class="empty"><h3>📭</h3><p>{}</p></div>'.format(msg), unsafe_allow_html=True)


def divider():
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


def sbadge(s):
    return '<span class="status-{s}">{su}</span>'.format(s=s, su=s.upper())


def pill_html(text, cls=""):
    c = " {}".format(cls) if cls else ""
    return '<span class="pill{c}">{t}</span>'.format(c=c, t=text)


def metrics_html(items):
    boxes = "".join(
        '<div class="metric-box"><div class="metric-num">{n}</div>'
        '<div class="metric-lbl">{l}</div></div>'.format(n=n, l=l)
        for n, l in items
    )
    st.markdown('<div class="metric-row">{}</div>'.format(boxes), unsafe_allow_html=True)


def mchtml(code, title, status, dt=""):
    return (
        '<div class="meeting-card">'
        '<div style="display:flex;justify-content:space-between;align-items:center">'
        '<div><span class="meeting-card-title">{title}</span>&nbsp;&nbsp;'
        '<span class="meeting-card-code">{code}</span>&nbsp;&nbsp;{badge}</div>'
        '<div class="meeting-card-date">{dt}</div>'
        '</div></div>'
    ).format(title=title, code=code, badge=sbadge(status), dt=dt)


def get_df(mc):
    rows = get_availability(mc)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows, columns=["Name", "Email", "Role", "Date", "Start Time", "End Time"])


def calc_matches(df, ol, pl):
    if df.empty:
        return []
    orgs = df[df["Role"] == ol]
    parts = df[df["Role"] == pl]
    out = []
    for _, o in orgs.iterrows():
        for _, p in parts.iterrows():
            if o["Date"] == p["Date"]:
                s = max(str(o["Start Time"]), str(p["Start Time"]))
                e = min(str(o["End Time"]), str(p["End Time"]))
                if s < e:
                    out.append({
                        "Date": o["Date"], "Start": s, "End": e,
                        "Organizer": o["Name"], "Participant": p["Name"],
                        "Participant Email": p.get("Email", "")
                    })
    return out


def calc_near_misses(df, ol, pl, max_gap_minutes=120):
    """
    Aynı tarihte örtüşmeyen ama max_gap_minutes'tan az fark olan slotlar.
    gap_min=999 olanları filtreler.
    """
    if df.empty:
        return []
    orgs = df[df["Role"] == ol]
    parts = df[df["Role"] == pl]
    near = []
    for _, o in orgs.iterrows():
        for _, p in parts.iterrows():
            if o["Date"] == p["Date"]:
                s = max(str(o["Start Time"]), str(p["Start Time"]))
                e = min(str(o["End Time"]), str(p["End Time"]))
                if s >= e:  # Örtüşme yok
                    gap_minutes = 999
                    try:
                        os_dt = datetime.strptime(str(o["Start Time"])[:5], "%H:%M")
                        oe_dt = datetime.strptime(str(o["End Time"])[:5], "%H:%M")
                        ps_dt = datetime.strptime(str(p["Start Time"])[:5], "%H:%M")
                        pe_dt = datetime.strptime(str(p["End Time"])[:5], "%H:%M")
                        gap1 = (ps_dt - oe_dt).total_seconds() / 60
                        gap2 = (os_dt - pe_dt).total_seconds() / 60
                        # Sadece pozitif gapleri al (gerçek boşluk)
                        gaps = [g for g in [gap1, gap2] if g > 0]
                        if gaps:
                            gap_minutes = min(gaps)
                        else:
                            gap_minutes = 999
                    except Exception:
                        gap_minutes = 999

                    # max_gap_minutes'tan büyük olanları filtrele
                    if gap_minutes <= max_gap_minutes:
                        near.append({
                            "Date": o["Date"],
                            "Org_Name": o["Name"],
                            "Org_Start": str(o["Start Time"]),
                            "Org_End": str(o["End Time"]),
                            "Part_Name": p["Name"],
                            "Part_Start": str(p["Start Time"]),
                            "Part_End": str(p["End Time"]),
                            "Gap_Min": round(gap_minutes)
                        })

    near.sort(key=lambda x: x["Gap_Min"])
    return near


def make_ics(title, ds, ss, es, desc="", vl=""):
    ss, es = str(ss), str(es)
    if len(ss) == 5:
        ss += ":00"
    if len(es) == 5:
        es += ":00"
    s = datetime.strptime("{} {}".format(ds, ss), "%Y-%m-%d %H:%M:%S")
    e = datetime.strptime("{} {}".format(ds, es), "%Y-%m-%d %H:%M:%S")
    st_ = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    fd = desc + ("\\nVideo: {}".format(vl) if vl else "")
    return (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//MeetAlign//EN\nBEGIN:VEVENT\n"
        "UID:{uid}@meetalign\nDTSTAMP:{stamp}\n"
        "DTSTART:{dtstart}\nDTEND:{dtend}\n"
        "SUMMARY:{title}\nDESCRIPTION:{desc}\nLOCATION:{loc}\n"
        "END:VEVENT\nEND:VCALENDAR"
    ).format(
        uid=st_, stamp=st_,
        dtstart=s.strftime("%Y%m%dT%H%M%S"),
        dtend=e.strftime("%Y%m%dT%H%M%S"),
        title=title, desc=fd, loc=vl or ""
    )


def send_resend(to, subj, body):
    ak = st.secrets.get("RESEND_API_KEY", "")
    se = st.secrets.get("SENDER_EMAIL", "")
    if not ak or not se:
        return False, "RESEND keys missing."
    try:
        r = requests.post(
            "https://api.resend.com/emails",
            json={
                "from": se, "to": [to],
                "subject": subj,
                "html": body.replace("\n", "<br>")
            },
            headers={
                "Authorization": "Bearer {}".format(ak),
                "Content-Type": "application/json"
            },
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
    return get_active_meetings() + get_confirmed_meetings()


def get_slots_for_ai(df, role_label):
    if df.empty:
        return []
    filtered = df[df["Role"] == role_label]
    return [
        {
            "Date": row["Date"],
            "Start": str(row["Start Time"]),
            "End": str(row["End Time"]),
            "Name": row["Name"]
        }
        for _, row in filtered.iterrows()
    ]


def proposal_status_badge(status):
    colors = {
        "pending": "pill-amber",
        "accepted": "pill-green",
        "rejected": "pill-red",
        "expired": "pill-gray",
    }
    return pill_html(status.upper(), colors.get(status, "pill-gray"))


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

pending_count = len(get_all_pending_proposals())
negotiate_label = t["negotiate"]
if pending_count > 0:
    negotiate_label = "{} 🔴{}".format(t["negotiate"], pending_count)

menu_items = [
    t["dashboard"], t["create"], t["availability"],
    negotiate_label, t["confirm"], t["chatbot"], t["manage"]
]

default_menu_idx = 0
if qc:
    default_menu_idx = 2

menu = st.sidebar.radio(t["menu"], menu_items, index=default_menu_idx)

if check_admin():
    st.sidebar.markdown("---")
    if st.sidebar.button("🔒 Logout Admin", key="sb_logout"):
        st.session_state["admin_auth"] = False
        st.rerun()

st.sidebar.markdown("---")
stats = get_meeting_stats()
st.sidebar.markdown(
    "**📊 Quick Stats**\n"
    "- 📋 Total: **{total}**\n"
    "- 🟢 Active: **{active}**\n"
    "- 🔵 Confirmed: **{confirmed}**\n"
    "- 📨 Pending: **{pending}**".format(
        total=stats["total"],
        active=stats["active"],
        confirmed=stats["confirmed"],
        pending=stats["pending_proposals"]
    )
)


# ═══════════════════════════════════════════════════════
# HERO
# ═══════════════════════════════════════════════════════
st.markdown(
    '<div class="hero">'
    '{avail} {cal} {ai} {zoom} {neg} {adm}'
    '<div class="hero-title">📅 {title}</div>'
    '<div class="hero-sub">{sub}</div>'
    '<div class="hero-steps">{steps}</div>'
    '</div>'.format(
        avail=pill_html("📋 Availability"),
        cal=pill_html("📅 Calendar"),
        ai=pill_html("🤖 AI"),
        zoom=pill_html("🎥 Zoom/Meet", "pill-green"),
        neg=pill_html("📨 Negotiate", "pill-purple"),
        adm=pill_html("⚙️ Admin", "pill-gray"),
        title=t["title"],
        sub=t["subtitle"],
        steps=t["hero"]
    ),
    unsafe_allow_html=True
)


# ═══════════════════════════════════════════════════════
# 0. DASHBOARD
# ═══════════════════════════════════════════════════════
if menu == t["dashboard"]:
    st.header("📊 {}".format(t["dashboard"]))

    stats = get_meeting_stats()
    metrics_html([
        (stats["total"], t["total"]),
        (stats["active"], t["active_meetings"]),
        (stats["confirmed"], t["confirmed_meetings"]),
        (stats["pending_proposals"], t["pending_proposals"]),
    ])

    pending_props = get_all_pending_proposals()
    if pending_props:
        card_open()
        st.markdown(
            '<div class="section-head">🔔 {} ({})</div>'.format(t["pending_proposals"], len(pending_props)),
            unsafe_allow_html=True
        )
        for pp in pending_props:
            st.markdown(
                '<div class="proposal-card">'
                '<strong>{title}</strong> — <code>{code}</code><br>'
                '📨 <strong>{name}</strong> proposed: <strong>{date}</strong> | {start}-{end}<br>'
                '<small style="color:#94a3b8">{created}</small>'
                '</div>'.format(
                    title=pp[2], code=pp[1], name=pp[3],
                    date=pp[4], start=pp[5], end=pp[6], created=pp[7]
                ),
                unsafe_allow_html=True
            )
        card_close()

    card_open()
    st.markdown('<div class="section-head">{}</div>'.format(t["existing_meetings"]), unsafe_allow_html=True)
    all_m = get_all_meetings()
    if all_m:
        for m in all_m[:12]:
            st.markdown(mchtml(m[0], m[1], m[2], m[3]), unsafe_allow_html=True)
    else:
        empty_state(t["no_meetings"])
    card_close()


# ═══════════════════════════════════════════════════════
# 1. CREATE MEETING
# ═══════════════════════════════════════════════════════
elif menu == t["create"]:
    st.header("🆕 {}".format(t["create"]))
    guide("1️⃣ Title & video link → 2️⃣ Your availability → 3️⃣ Create → 4️⃣ Share")

    card_open()
    st.markdown('<div class="section-head">📝 Meeting Details</div>', unsafe_allow_html=True)
    mt = st.text_input(t["meeting_title"], placeholder=t["meeting_placeholder"])
    vl = st.text_input(t["meeting_video_link"], placeholder=t["meeting_video_placeholder"])

    divider()
    st.markdown('<div class="section-head">{}</div>'.format(t["org_info"]), unsafe_allow_html=True)
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

    divider()
    st.markdown("**➕ Add more availability slots (optional)**")

    if "extra_org_slots" not in st.session_state:
        st.session_state["extra_org_slots"] = []

    if st.button("➕ Add Another Time Slot", key="add_extra_slot"):
        st.session_state["extra_org_slots"].append({})

    extra_slots = []
    for idx, _ in enumerate(st.session_state["extra_org_slots"]):
        with st.expander("📅 Extra Slot #{}".format(idx + 1), expanded=True):
            ec1, ec2 = st.columns(2)
            with ec1:
                ed = st.date_input("Date #{}".format(idx + 1), key="cr_ed_{}".format(idx))
            with ec2:
                esc1, esc2 = st.columns(2)
                with esc1:
                    es_t = st.time_input("Start #{}".format(idx + 1), key="cr_es_{}".format(idx))
                with esc2:
                    ee_t = st.time_input("End #{}".format(idx + 1), key="cr_ee_{}".format(idx))
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
            ml = "{}?meeting={}".format(base_url(), mc)
            add_availability(mc, org_name, org_email, t["organizer"], org_date, org_start, org_end)
            for es in extra_slots:
                if es["start"] < es["end"]:
                    add_availability(mc, org_name, org_email, t["organizer"],
                                     es["date"], es["start"], es["end"])
            st.session_state["extra_org_slots"] = []
            st.success(t["created"])
            c1, c2 = st.columns([1, 2])
            with c1:
                st.text_input(t["meeting_code"], value=mc, disabled=True, key="cr_mc")
            with c2:
                st.text_input(t["meeting_link"], value=ml, disabled=True, key="cr_ml")
            if vl:
                st.markdown(
                    '<div class="link-box">🎥 <a href="{vl}" target="_blank">{vl}</a></div>'.format(vl=vl),
                    unsafe_allow_html=True
                )
            slot_info = "📅 {} | {}-{}".format(org_date, org_start, org_end)
            for es in extra_slots:
                if es["start"] < es["end"]:
                    slot_info += "\n📅 {} | {}-{}".format(es["date"], es["start"], es["end"])
            st.info("👤 {}\n{}".format(org_name, slot_info))
            divider()
            st.subheader(t["copy_invitation"])
            vline = "\nVideo: {}".format(vl) if vl else ""
            st.code(
                "Hello,\n\nMeeting: {title}\nLink: {ml}\nCode: {mc}{vl}\n\n"
                "Organizer: {org}\n{slots}\n\nBest regards".format(
                    title=mt, ml=ml, mc=mc, vl=vline, org=org_name, slots=slot_info
                )
            )
    card_close()


# ═══════════════════════════════════════════════════════
# 2. ADD AVAILABILITY
# ═══════════════════════════════════════════════════════
elif menu == t["availability"]:
    st.header("📝 {}".format(t["availability"]))
    guide("1️⃣ Select meeting → 2️⃣ Fill details → 3️⃣ Save (multiple slots allowed)")

    avail_list = all_meetings_for_select()
    card_open()
    st.markdown('<div class="section-head">{}</div>'.format(t["existing_meetings"]), unsafe_allow_html=True)
    if avail_list:
        for m in avail_list:
            st.markdown(mchtml(m[0], m[1], m[2], m[3]), unsafe_allow_html=True)
    else:
        empty_state(t["no_meetings"])

    options_codes = [m[0] for m in avail_list] if avail_list else []
    options_labels = {m[0]: "📋 {} — {}".format(m[0], m[1]) for m in avail_list} if avail_list else {}

    default_idx = 0
    if qc and qc.upper() in [c.upper() for c in options_codes]:
        for i, c in enumerate(options_codes):
            if c.upper() == qc.upper():
                default_idx = i + 1
                break

    sel_meeting = st.selectbox(
        t["select_meeting"], [""] + options_codes,
        index=default_idx,
        format_func=lambda x: options_labels.get(x, "— {} —".format(t["enter_code"])) if x else "— {} —".format(t["enter_code"]),
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
        st.success("📋 {}".format(meeting[1]))
        st.markdown("{}: {}".format(t["status"], sbadge(meeting[2])), unsafe_allow_html=True)
        if meeting[7]:
            st.markdown(
                '<div class="link-box">🎥 <a href="{vl}" target="_blank">{vl}</a></div>'.format(vl=meeting[7]),
                unsafe_allow_html=True
            )

        edf = get_df(mc)
        if not edf.empty:
            divider()
            st.markdown('<div class="section-head">📊 {}</div>'.format(t["all_availability"]), unsafe_allow_html=True)
            metrics_html([(len(edf), t["entries"]), (edf["Email"].nunique(), t["people"])])
            st.dataframe(edf, use_container_width=True, hide_index=True)

            matches = calc_matches(edf, t["organizer"], t["participant"])
            if matches:
                st.markdown(
                    '<div class="section-head">✅ {} ({})</div>'.format(t["matches"], len(matches)),
                    unsafe_allow_html=True
                )
                for m_item in matches:
                    st.markdown(
                        '{d} {time} {org} ↔ {part}'.format(
                            d=pill_html(m_item["Date"], "pill-green"),
                            time=pill_html("{}-{}".format(m_item["Start"], m_item["End"]), "pill-green"),
                            org=m_item["Organizer"],
                            part=m_item["Participant"]
                        ),
                        unsafe_allow_html=True
                    )
            else:
                st.warning(t["no_match"])
                near = calc_near_misses(edf, t["organizer"], t["participant"])
                if near:
                    st.markdown(
                        '<div class="section-head">{}</div>'.format(t["near_misses"]),
                        unsafe_allow_html=True
                    )
                    for n in near[:5]:
                        st.markdown(
                            "📅 **{date}**: {on} {os}–{oe} | {pn} {ps}–{pe} ⏱️ {gap} min gap".format(
                                date=n["Date"],
                                on=n["Org_Name"], os=n["Org_Start"], oe=n["Org_End"],
                                pn=n["Part_Name"], ps=n["Part_Start"], pe=n["Part_End"],
                                gap=n["Gap_Min"]
                            )
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

        if "avail_extra_slots" not in st.session_state:
            st.session_state["avail_extra_slots"] = []
        if st.button("➕ Add Another Slot", key="av_add_extra"):
            st.session_state["avail_extra_slots"].append({})

        av_extras = []
        for idx, _ in enumerate(st.session_state["avail_extra_slots"]):
            with st.expander("📅 Extra Slot #{}".format(idx + 1), expanded=True):
                aec1, aec2 = st.columns(2)
                with aec1:
                    aed = st.date_input("Date #{}".format(idx + 1), key="av_ed_{}".format(idx))
                with aec2:
                    aes1, aes2 = st.columns(2)
                    with aes1:
                        aes_t = st.time_input("Start #{}".format(idx + 1), key="av_es_{}".format(idx))
                    with aes2:
                        aee_t = st.time_input("End #{}".format(idx + 1), key="av_ee_{}".format(idx))
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
# 3. NEGOTIATE & PROPOSE — YENİDEN YAZILMIŞ (TABS)
# ═══════════════════════════════════════════════════════
elif menu == negotiate_label:
    st.header("📨 {}".format(t["negotiate"]))
    guide("🔄 No match? Get AI suggestions, propose dates, manage proposals, or postpone.")

    avail_list = all_meetings_for_select()
    card_open()
    options_codes = [m[0] for m in avail_list] if avail_list else []
    options_labels = {m[0]: "📋 {} — {}".format(m[0], m[1]) for m in avail_list} if avail_list else {}

    default_idx = 0
    if qc and qc.upper() in [c.upper() for c in options_codes]:
        for i, c in enumerate(options_codes):
            if c.upper() == qc.upper():
                default_idx = i + 1
                break

    sel = st.selectbox(
        t["select_meeting"], [""] + options_codes, index=default_idx,
        format_func=lambda x: options_labels.get(x, "— {} —".format(t["enter_code"])) if x else "— {} —".format(t["enter_code"]),
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
    vlink = meeting[7] if len(meeting) > 7 else (meeting[3] if len(meeting) > 3 else "")

    # Durum özeti
    df = get_df(mc)
    matches = calc_matches(df, t["organizer"], t["participant"]) if not df.empty else []
    proposals = get_proposals(mc)
    pending_props = [p for p in proposals if p[7] == "pending"]
    near_misses = calc_near_misses(df, t["organizer"], t["participant"]) if not df.empty else []

    # Tab sayısına göre etiket (bekleyen teklif varsa badge ekle)
    tab_proposals_label = t["tab_proposals"]
    if pending_props:
        tab_proposals_label = "{} 🔴{}".format(t["tab_proposals"], len(pending_props))

    tabs = st.tabs([
        t["tab_status"],
        t["tab_ai"],
        t["tab_propose"],
        tab_proposals_label,
        t["tab_postpone"]
    ])

    # ──────────────────────────────────────────
    # TAB 1: STATUS
    # ──────────────────────────────────────────
    with tabs[0]:
        card_open()
        st.markdown(
            "### 📋 {title} &nbsp; {badge}".format(title=mtitle, badge=sbadge(meeting[2])),
            unsafe_allow_html=True
        )
        if vlink:
            st.markdown(
                '<div class="link-box">🎥 <a href="{vl}" target="_blank">{vl}</a></div>'.format(vl=vlink),
                unsafe_allow_html=True
            )

        if df.empty:
            empty_state(t["no_data"])
            card_close()
        else:
            metrics_html([
                (len(df), t["entries"]),
                (len(matches), t["match_count"]),
                (len(near_misses), "Near Misses"),
                (len(pending_props), t["pending_proposals"])
            ])

            if matches:
                st.success("✅ {} matching slot(s) found!".format(len(matches)))
                mdf = pd.DataFrame(matches)
                st.dataframe(mdf, use_container_width=True, hide_index=True)
                st.markdown(
                    '<div class="action-hint">💡 Matching slots found! Go to <strong>Confirm & Calendar</strong> to finalize.</div>',
                    unsafe_allow_html=True
                )
                if st.button(t["go_confirm"], use_container_width=True, key="neg_go_confirm"):
                    st.info("Go to **{}** in the sidebar.".format(t["confirm"]))
            else:
                st.warning("⚠️ {}".format(t["no_match"]))
                st.markdown(
                    '<div class="action-hint">{}</div>'.format(t["no_match_help"].replace("\n", "<br>")),
                    unsafe_allow_html=True
                )

            divider()
            st.markdown('<div class="section-head">📊 {}</div>'.format(t["all_availability"]), unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, hide_index=True)
            card_close()

    # ──────────────────────────────────────────
    # TAB 2: AI & NEAR MISSES
    # ──────────────────────────────────────────
    with tabs[1]:
        card_open()

        # Near Misses (120 dk filtreli)
        st.markdown('<div class="section-head">{}</div>'.format(t["near_misses"]), unsafe_allow_html=True)
        if near_misses:
            for n in near_misses[:6]:
                shift_hint = "{} {} {}".format(t["shift_suggest"], n["Gap_Min"], t["minutes"])
                st.markdown(
                    '<div class="near-miss-card">'
                    '<strong>📅 {date}</strong><br>'
                    '👤 {on}: <code>{os}–{oe}</code><br>'
                    '👤 {pn}: <code>{ps}–{pe}</code><br>'
                    '<span style="color:#c2410c;font-weight:600">⏱️ {gap} min gap — {hint}</span>'
                    '</div>'.format(
                        date=n["Date"],
                        on=n["Org_Name"], os=n["Org_Start"][:5], oe=n["Org_End"][:5],
                        pn=n["Part_Name"], ps=n["Part_Start"][:5], pe=n["Part_End"][:5],
                        gap=n["Gap_Min"], hint=shift_hint
                    ),
                    unsafe_allow_html=True
                )
        else:
            if df.empty:
                st.info("No availability data yet.")
            else:
                st.info("No near misses within 120 minutes found.")

        divider()

        # AI Suggestions
        st.markdown('<div class="section-head">{}</div>'.format(t["ai_suggest"]), unsafe_allow_html=True)

        if st.button(t["ai_suggest_btn"], key="neg_ai_btn", use_container_width=True):
            with st.spinner(t["generating"]):
                try:
                    org_slots = get_slots_for_ai(df, t["organizer"]) if not df.empty else []
                    part_slots = get_slots_for_ai(df, t["participant"]) if not df.empty else []
                    suggestions = suggest_alternative_dates(org_slots, part_slots, mtitle, lang)
                    # session_state anahtarı: meeting code bazlı — kaybolmaz
                    st.session_state["neg_suggestions_{}".format(mc)] = suggestions
                except Exception as e:
                    st.error("Error: {}".format(e))

        suggestions_key = "neg_suggestions_{}".format(mc)
        if suggestions_key in st.session_state and st.session_state[suggestions_key]:
            st.markdown(
                '<div class="suggestion-box">'
                '<div class="suggestion-title">🤖 {}</div>'
                '<div style="font-size:14px;line-height:1.7;color:#3730a3">{}</div>'
                '</div>'.format(
                    t["ai_suggest"],
                    str(st.session_state[suggestions_key]).replace("\n", "<br>")
                ),
                unsafe_allow_html=True
            )
            # AI önerisinden direkt teklif
            st.markdown("---")
            st.markdown("**💡 Propose one of the AI suggestions directly:**")
            if st.button("📨 Use AI suggestion as proposal", key="ai_to_prop"):
                st.session_state["neg_prefill_note"] = str(st.session_state[suggestions_key])[:200]
                st.info("Switch to the **{}** tab and fill in the date.".format(t["tab_propose"]))
        else:
            st.caption("Click the button above to get AI-powered suggestions.")

        card_close()

    # ──────────────────────────────────────────
    # TAB 3: PROPOSE NEW DATE
    # ──────────────────────────────────────────
    with tabs[2]:
        card_open()
        st.markdown('<div class="section-head">{}</div>'.format(t["propose_new"]), unsafe_allow_html=True)
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

        prefill_note = st.session_state.get("neg_prefill_note", "")
        prop_note = st.text_area(
            t["response_note"],
            value=prefill_note,
            key="prop_note",
            placeholder="Optional: reason or context for this proposal"
        )

        # "Aynı zamanda availability olarak da ekle" checkbox
        also_add_avail = st.checkbox(
            "Also add this as my availability slot",
            value=True, key="prop_also_avail"
        )

        st.markdown("")
        if st.button(t["propose_button"], use_container_width=True, key="prop_send"):
            if not prop_name:
                st.warning(t["enter_name"])
            elif prop_start >= prop_end:
                st.warning(t["time_error"])
            else:
                create_proposal(mc, prop_name, prop_email, prop_role, prop_date, prop_start, prop_end, prop_note)
                if also_add_avail:
                    add_availability(mc, prop_name, prop_email, prop_role, prop_date, prop_start, prop_end)
                if "neg_prefill_note" in st.session_state:
                    del st.session_state["neg_prefill_note"]
                st.success(t["proposal_sent"])
                st.rerun()

        card_close()

    # ──────────────────────────────────────────
    # TAB 4: ALL PROPOSALS & ACTIONS
    # ──────────────────────────────────────────
    with tabs[3]:
        card_open()
        st.markdown(
            '<div class="section-head">{} ({})</div>'.format(t["proposals"], len(proposals)),
            unsafe_allow_html=True
        )

        if not proposals:
            empty_state(t["no_proposals"])
        else:
            for prop in proposals:
                (pid, pname, pemail, prole, pdate, pstart, pend,
                 pstatus, pnote, presp, pcreated) = prop

                card_cls = "proposal-card"
                if pstatus == "accepted":
                    card_cls += " proposal-accepted"
                elif pstatus == "rejected":
                    card_cls += " proposal-rejected"
                elif pstatus == "expired":
                    card_cls += " proposal-expired"

                note_html = "<br>📝 <em>{}</em>".format(pnote) if pnote else ""
                resp_html = "<br>💬 <em>{}</em>".format(presp) if presp else ""

                # Timeline dot
                dot_class = "dot-{}".format(pstatus)

                st.markdown(
                    '<div class="{cls}">'
                    '<span class="timeline-dot {dot}"></span>'
                    '<strong>📨 {name}</strong> <span style="color:#94a3b8">({role})</span> — '
                    '{badge}<br>'
                    '📅 <strong>{date}</strong> | ⏰ <strong>{start}–{end}</strong><br>'
                    '<small style="color:#94a3b8">Created: {created}</small>'
                    '{note}{resp}'
                    '</div>'.format(
                        cls=card_cls, dot=dot_class,
                        name=pname, role=prole,
                        badge=proposal_status_badge(pstatus),
                        date=pdate, start=str(pstart)[:5], end=str(pend)[:5],
                        created=pcreated,
                        note=note_html, resp=resp_html
                    ),
                    unsafe_allow_html=True
                )

                # Bekleyen teklifler için aksiyonlar
                if pstatus == "pending":
                    resp_note = st.text_input(
                        t["response_note"],
                        key="resp_note_{}".format(pid),
                        placeholder="Optional response note"
                    )

                    bcol1, bcol2, bcol3 = st.columns(3)

                    with bcol1:
                        if st.button(t["accept"], key="acc_{}".format(pid), use_container_width=True):
                            update_proposal(pid, "accepted", resp_note, "admin")
                            st.success(t["proposal_accepted"])
                            st.rerun()

                    with bcol2:
                        if st.button(
                            t["confirm_from_proposal"],
                            key="conf_prop_{}".format(pid),
                            use_container_width=True
                        ):
                            update_proposal(pid, "accepted", resp_note, "admin")
                            # Diğer pending'leri expire et
                            expire_other_proposals(mc, pid)
                            # Toplantıyı onayla
                            confirm_meeting_slot(mc, pdate, pstart, pend)
                            # Uygunluk tablosuna da ekle
                            add_availability(
                                mc, pname, pemail, prole, pdate, pstart, pend
                            )
                            st.success("✅ {} {}".format(t["confirmed"], "— {} {} {}-{}".format(pdate, pname, pstart, pend)))
                            st.balloons()
                            st.rerun()

                    with bcol3:
                        if st.button(t["reject"], key="rej_{}".format(pid), use_container_width=True):
                            update_proposal(pid, "rejected", resp_note, "admin")
                            st.warning(t["proposal_rejected"])
                            st.rerun()

                    # Counter-propose section
                    with st.expander("🔄 {} — {}".format(t["counter"], t["counter_hint"]), expanded=False):
                        cpc1, cpc2 = st.columns(2)
                        with cpc1:
                            counter_date = st.date_input("Date", key="ctr_date_{}".format(pid))
                        with cpc2:
                            cpc3, cpc4 = st.columns(2)
                            with cpc3:
                                counter_start = st.time_input("Start", key="ctr_start_{}".format(pid))
                            with cpc4:
                                counter_end = st.time_input("End", key="ctr_end_{}".format(pid))
                        counter_note = st.text_input("Note", key="ctr_note_{}".format(pid))
                        counter_name = st.text_input("Your name", key="ctr_name_{}".format(pid), placeholder="Organizer")

                        if st.button(t["counter_propose"], key="ctr_btn_{}".format(pid), use_container_width=True):
                            if counter_start >= counter_end:
                                st.warning(t["time_error"])
                            else:
                                # Original'ı reject et
                                update_proposal(pid, "rejected", "Counter-proposed", "admin")
                                # Yeni counter proposal oluştur
                                create_proposal(
                                    mc,
                                    counter_name or "Organizer",
                                    "",
                                    t["organizer"],
                                    counter_date,
                                    counter_start,
                                    counter_end,
                                    counter_note or "Counter-proposal",
                                    counter_of=pid
                                )
                                st.success("🔄 Counter-proposal sent!")
                                st.rerun()

                st.markdown("<hr style='border:none;border-top:1px solid #f1f5f9;margin:8px 0'>", unsafe_allow_html=True)

        card_close()

    # ──────────────────────────────────────────
    # TAB 5: POSTPONE / RESCHEDULE
    # ──────────────────────────────────────────
    with tabs[4]:
        card_open()
        st.markdown(
            '<div class="section-head">⏸️ {} / {}</div>'.format(t["postpone"], t["reschedule"]),
            unsafe_allow_html=True
        )

        mstatus = meeting[2]
        st.markdown(
            "Current status: {}".format(sbadge(mstatus)),
            unsafe_allow_html=True
        )

        divider()

        # Postpone — active ve confirmed her ikisinde çalışır
        st.markdown("**⏸️ {}**".format(t["postpone"]))
        st.caption("Resets meeting to active. Keeps existing availability slots.")
        pp_reason = st.text_input(t["postpone_reason"], key="pp_reason_tab",
                                  placeholder="e.g. Need more participants")

        if st.button(t["postpone"], key="pp_btn_tab", use_container_width=True):
            if mstatus in ("active", "confirmed"):
                # Sadece status sıfırla, uygunlukları koru
                from database import _conn, _log
                c2 = _conn()
                c2.execute(
                    "UPDATE meetings SET status='active', confirmed_date=NULL, "
                    "confirmed_start=NULL, confirmed_end=NULL WHERE code=?",
                    (mc,)
                )
                c2.execute(
                    "UPDATE proposals SET status='expired' WHERE meeting_code=? AND status='pending'",
                    (mc,)
                )
                c2.commit()
                c2.close()
                _log(mc, "postponed_keep_avail", pp_reason)
                st.warning("⏸️ {}".format(t["postponed"]))
                st.rerun()
            else:
                st.info("Meeting is already in {} status.".format(mstatus))

        divider()

        # Full Reschedule — uygunlukları siler
        st.markdown("**🔄 {}**".format(t["reschedule"]))
        st.caption(t["avail_warning"])

        # Opsiyonel: eski uygunlukları temizleyip temizlememe
        clear_avail_opt = st.checkbox(
            t["clear_avail"],
            value=True,
            key="resc_clear_opt"
        )
        resc_reason = st.text_input("Reschedule reason", key="resc_reason",
                                    placeholder="e.g. Key participant unavailable")

        if st.button(t["reschedule"], key="resc_btn_tab", use_container_width=True):
            if clear_avail_opt:
                postpone_meeting(mc, resc_reason or "Rescheduled")
            else:
                from database import _conn, _log
                c2 = _conn()
                c2.execute(
                    "UPDATE meetings SET status='active', confirmed_date=NULL, "
                    "confirmed_start=NULL, confirmed_end=NULL WHERE code=?",
                    (mc,)
                )
                c2.execute(
                    "UPDATE proposals SET status='expired' WHERE meeting_code=? AND status='pending'",
                    (mc,)
                )
                c2.commit()
                c2.close()
                _log(mc, "rescheduled", resc_reason or "")
            st.warning("🔄 {}".format(t["postponed"]))
            st.rerun()

        card_close()


# ═══════════════════════════════════════════════════════
# 4. CONFIRM & CALENDAR
# ═══════════════════════════════════════════════════════
elif menu == t["confirm"]:
    st.header("✅ {}".format(t["confirm"]))
    guide("1️⃣ Select meeting → 2️⃣ View matches → 3️⃣ Confirm → 4️⃣ .ics / Email")

    avail_list = all_meetings_for_select()
    card_open()
    options_codes = [m[0] for m in avail_list] if avail_list else []
    options_labels = {m[0]: "📋 {} — {}".format(m[0], m[1]) for m in avail_list} if avail_list else {}
    default_idx = 0
    if qc and qc.upper() in [c.upper() for c in options_codes]:
        for i, c in enumerate(options_codes):
            if c.upper() == qc.upper():
                default_idx = i + 1
                break

    sel = st.selectbox(
        t["select_meeting"], [""] + options_codes, index=default_idx,
        format_func=lambda x: options_labels.get(x, "— {} —".format(t["enter_code"])) if x else "— {} —".format(t["enter_code"]),
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

    mtitle = meeting[1]
    mstatus = meeting[2]
    vlink = meeting[7] if len(meeting) > 7 else ""

    card_open()
    st.success("📋 {}".format(mtitle))
    st.markdown("{}: {}".format(t["status"], sbadge(mstatus)), unsafe_allow_html=True)

    # Video link
    st.markdown("### {}".format(t["video_link"]))
    if vlink:
        st.markdown(
            '<div class="link-box">🎥 <a href="{vl}" target="_blank">{vl}</a></div>'.format(vl=vlink),
            unsafe_allow_html=True
        )
    else:
        st.info(t["no_video_link"])
    nvl = st.text_input(t["meeting_video_link"], value=vlink or "", key="upd_vl",
                        placeholder=t["meeting_video_placeholder"])
    if st.button(t["update_link"], key="btn_upd"):
        update_meeting_link(mc, nvl)
        st.success(t["link_updated"])
        st.rerun()

    # Already confirmed
    if mstatus == "confirmed":
        divider()
        st.markdown(
            '<div class="confirmed-banner">'
            '<h3>✅ {}</h3>'
            '<p>📅 {} | ⏰ {}–{}</p>'
            '</div>'.format(
                t["already_confirmed"],
                meeting[4], meeting[5], meeting[6]
            ),
            unsafe_allow_html=True
        )
        ics = make_ics(mtitle, meeting[4], meeting[5], meeting[6], "MeetAlign: {}".format(mc), vlink)
        st.download_button(
            t["download_ics"], data=ics,
            file_name="meetalign_{}.ics".format(mc),
            mime="text/calendar", use_container_width=True
        )

        divider()
        st.markdown('<div class="section-head">✉️ {}</div>'.format(t["generate_confirm_email"]), unsafe_allow_html=True)
        re_conf = st.text_input(t["recipient_email"], key="conf_re_confirmed")
        if st.button(t["generate_confirm_email"], key="gen_conf_confirmed"):
            with st.spinner(t["generating"]):
                try:
                    ab = generate_confirmation_email(
                        mtitle, meeting[4], meeting[5], meeting[6],
                        language=lang, meeting_link=vlink or ""
                    )
                    st.session_state["conf_body"] = ab
                except Exception as e:
                    st.error("Error: {}".format(e))

        ebody = st.text_area(
            "Email Preview",
            value=st.session_state.get(
                "conf_body",
                "Meeting: {}\nDate: {}\nTime: {}-{}".format(mtitle, meeting[4], meeting[5], meeting[6])
            ),
            height=220, key="conf_ta_confirmed"
        )
        if st.button(t["send_email"], use_container_width=True, key="btn_send_confirmed"):
            if not re_conf:
                st.warning(t["recipient_email"])
            else:
                ok, msg = send_resend(re_conf, "Confirmed: {}".format(mtitle), ebody)
                if ok:
                    st.success(t["email_sent"])
                else:
                    st.error("{} {}".format(t["email_failed"], msg))
        card_close()
        st.stop()

    # Not confirmed — show availability and matches
    df = get_df(mc)
    if df.empty:
        empty_state(t["no_data"])
        card_close()
        st.stop()

    divider()
    st.subheader(t["all_availability"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    matches = calc_matches(df, t["organizer"], t["participant"])
    st.subheader(t["matches"])

    if not matches:
        st.warning(t["no_match"])
        st.markdown(
            "💡 Go to **{}** page to get AI suggestions or propose new dates.".format(t["negotiate"])
        )
        card_close()
        st.stop()

    metrics_html([
        (len(df), t["entries"]),
        (len(matches), t["match_count"]),
        (df["Email"].nunique(), t["people"])
    ])
    mdf = pd.DataFrame(matches)
    st.dataframe(mdf, use_container_width=True, hide_index=True)

    divider()
    st.markdown('<div class="section-head">{}</div>'.format(t["generate_invite"]), unsafe_allow_html=True)
    if st.button(t["generate_invite"], key="gen_inv"):
        with st.spinner(t["generating"]):
            try:
                ie = generate_meeting_email(mtitle, matches, language=lang, meeting_link=vlink or "")
                st.session_state["inv_email"] = ie
            except Exception as e:
                st.error("Error: {}".format(e))

    if "inv_email" in st.session_state and st.session_state["inv_email"]:
        st.subheader(t["generated_email"])
        st.text_area("", value=st.session_state["inv_email"], height=260, key="inv_ta")

    divider()
    si = st.selectbox(
        t["select_slot"], range(len(matches)),
        format_func=lambda i: "📅 {} | ⏰ {}-{} ({} ↔ {})".format(
            matches[i]["Date"], matches[i]["Start"], matches[i]["End"],
            matches[i]["Organizer"], matches[i]["Participant"]
        )
    )
    sel_m = matches[si]
    st.markdown(
        "### ✅ **{}** | **{}** – **{}**".format(sel_m["Date"], sel_m["Start"], sel_m["End"])
    )
    st.markdown("👤 {} ↔ {}".format(sel_m["Organizer"], sel_m["Participant"]))

    if st.button(t["confirm_meeting"], use_container_width=True, key="btn_confirm"):
        confirm_meeting_slot(mc, sel_m["Date"], sel_m["Start"], sel_m["End"])
        # Diğer pending teklifleri expire et
        for p in get_pending_proposals(mc):
            update_proposal(p[0], "expired", "Meeting confirmed via availability match", "system")
        st.success(t["confirmed"])
        st.balloons()
        ics = make_ics(mtitle, sel_m["Date"], sel_m["Start"], sel_m["End"],
                       "MeetAlign: {}".format(mc), vlink)
        st.download_button(
            t["download_ics"], data=ics,
            file_name="meetalign_{}.ics".format(mc),
            mime="text/calendar", use_container_width=True
        )

    divider()
    st.markdown('<div class="section-head">✉️ {}</div>'.format(t["generate_confirm_email"]), unsafe_allow_html=True)
    re_email = st.text_input(t["recipient_email"], value=sel_m.get("Participant Email", ""), key="conf_re")
    if st.button(t["generate_confirm_email"], key="gen_conf"):
        with st.spinner(t["generating"]):
            try:
                ab = generate_confirmation_email(
                    mtitle, sel_m["Date"], sel_m["Start"], sel_m["End"],
                    language=lang, meeting_link=vlink or ""
                )
                st.session_state["conf_body"] = ab
            except Exception as e:
                st.error("Error: {}".format(e))

    ebody = st.text_area(
        "Email Preview",
        value=st.session_state.get(
            "conf_body",
            "Meeting: {}\nDate: {}\nTime: {}-{}\n\nClick Generate above for AI email.".format(
                mtitle, sel_m["Date"], sel_m["Start"], sel_m["End"]
            )
        ),
        height=220, key="conf_ta"
    )
    if st.button(t["send_email"], use_container_width=True, key="btn_send"):
        if not re_email:
            st.warning(t["recipient_email"])
        else:
            ok, msg = send_resend(re_email, "Confirmed: {}".format(mtitle), ebody)
            if ok:
                st.success(t["email_sent"])
            else:
                st.error("{} {}".format(t["email_failed"], msg))
    card_close()


# ═══════════════════════════════════════════════════════
# 5. AI CHATBOT
# ═══════════════════════════════════════════════════════
elif menu == t["chatbot"]:
    st.header("🤖 {}".format(t["chatbot"]))
    guide(t["chat_help"])

    card_open()
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    mode = st.radio(t["chat_mode"], [t["mode_command"], t["mode_chat"]], horizontal=True)

    for ch in st.session_state["chat_history"]:
        if ch["role"] == "user":
            st.markdown("**🧑 You:** {}".format(ch["text"]))
        else:
            st.markdown("**🤖 AI:** {}".format(ch["text"]))
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
                    st.session_state["chat_history"].append({"role": "ai", "text": "Error: {}".format(err)})
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
                        except Exception:
                            etv = ""
                    mc2 = create_meeting(mt2)
                    ml2 = "{}?meeting={}".format(base_url(), mc2)
                    st.success(t["created"])
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.text_input(t["meeting_code"], value=mc2, key="ch_mc", disabled=True)
                    with c2:
                        st.text_input(t["meeting_link"], value=ml2, key="ch_ml", disabled=True)
                    if dv and stv and etv:
                        add_availability(
                            mc2, "Organizer", "", t["organizer"], dv,
                            "{}:00".format(stv) if len(stv) == 5 else stv,
                            "{}:00".format(etv) if len(etv) == 5 else etv
                        )
                        st.info("✅ Organizer availability added.")
                    st.subheader(t["copy_invitation"])
                    st.code(
                        "Hello {pn},\n\nMeeting: {mt}\nLink: {ml}\nCode: {mc}\n\nBest regards".format(
                            pn=pn, mt=mt2, ml=ml2, mc=mc2
                        )
                    )
                    st.session_state["chat_history"].append(
                        {"role": "ai", "text": "Created: {} | {}".format(mt2, mc2)}
                    )

    if st.session_state["chat_history"]:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state["chat_history"] = []
            st.rerun()
    card_close()


# ═══════════════════════════════════════════════════════
# 6. MANAGE MEETINGS (ADMIN)
# ═══════════════════════════════════════════════════════
elif menu == t["manage"]:
    st.header("⚙️ {}".format(t["manage"]))

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
        st.markdown('<div class="admin-locked">{}</div>'.format(t["admin_locked"]), unsafe_allow_html=True)
        st.stop()

    st.markdown('<div class="admin-success">🔓 {}</div>'.format(t["admin_logged"]), unsafe_allow_html=True)
    guide("Select any meeting below to manage. Cancel, archive, restore, postpone or permanently delete.")

    all_m = get_all_meetings()
    if not all_m:
        empty_state(t["no_meetings"])
        st.stop()

    stats = get_meeting_stats()
    metrics_html([
        (stats["total"], t["total"]),
        (stats["active"], t["active_meetings"]),
        (stats["confirmed"], t["confirmed_meetings"]),
        (stats["pending_proposals"], t["pending_proposals"]),
    ])

    card_open()
    tabs_m = st.tabs([t["active_meetings"], t["confirmed_meetings"], t["archived_meetings"]])

    with tabs_m[0]:
        actives = get_active_meetings()
        if actives:
            for m in actives:
                st.markdown(mchtml(m[0], m[1], m[2], m[3]), unsafe_allow_html=True)
        else:
            empty_state(t["no_meetings"])

    with tabs_m[1]:
        confirmed_list = get_confirmed_meetings()
        if confirmed_list:
            for m in confirmed_list:
                st.markdown(mchtml(m[0], m[1], m[2], m[3]), unsafe_allow_html=True)
        else:
            empty_state(t["no_meetings"])

    with tabs_m[2]:
        archived = get_archived_meetings()
        if archived:
            for a in archived:
                reason_html = " — <em>{}</em>".format(a[4]) if a[4] else ""
                st.markdown(
                    '<div class="meeting-card" style="border-color:#fecaca">'
                    '<div style="display:flex;justify-content:space-between;align-items:center">'
                    '<div><span class="meeting-card-title">{title}</span>&nbsp;'
                    '<span class="meeting-card-code">{code}</span>{reason}</div>'
                    '<div class="meeting-card-date">{dt}</div>'
                    '</div></div>'.format(
                        title=a[1], code=a[0], reason=reason_html, dt=a[3]
                    ),
                    unsafe_allow_html=True
                )
        else:
            empty_state(t["no_meetings"])

    divider()
    labels = {m[0]: "{} ({}) [{}]".format(m[1], m[0], m[2]) for m in all_m}
    sel_code = st.selectbox(
        t["select_to_manage"],
        [m[0] for m in all_m],
        format_func=lambda x: labels.get(x, x),
        key="manage_sel"
    )
    card_close()

    meeting = get_meeting(sel_code) if sel_code else None

    if meeting:
        card_open()
        st.markdown('<div class="section-head">📋 {}</div>'.format(t["meeting_details"]), unsafe_allow_html=True)
        st.markdown("### {}".format(meeting[1]))
        st.markdown(
            "**Code:** `{code}` &nbsp;&nbsp; {st}: {badge}".format(
                code=sel_code, st=t["status"], badge=sbadge(meeting[2])
            ),
            unsafe_allow_html=True
        )
        if meeting[7]:
            st.markdown(
                '<div class="link-box">🎥 <a href="{vl}" target="_blank">{vl}</a></div>'.format(vl=meeting[7]),
                unsafe_allow_html=True
            )
        if meeting[2] == "confirmed" and meeting[4]:
            st.info("📅 Confirmed: {} | {}-{}".format(meeting[4], meeting[5], meeting[6]))

        # Uygunluklar
        edf = get_df(sel_code)
        if not edf.empty:
            divider()
            st.markdown(
                '<div class="section-head">📊 {}</div>'.format(t["all_availability"]),
                unsafe_allow_html=True
            )
            metrics_html([(len(edf), t["entries"]), (edf["Email"].nunique(), t["people"])])
            st.dataframe(edf, use_container_width=True, hide_index=True)

        # Teklifler
        mg_proposals = get_proposals(sel_code)
        if mg_proposals:
            divider()
            st.markdown(
                '<div class="section-head">{} ({})</div>'.format(t["proposals"], len(mg_proposals)),
                unsafe_allow_html=True
            )
            for prop in mg_proposals:
                (pid, pname, pemail, prole, pdate, pstart, pend,
                 pstatus, pnote, presp, pcreated) = prop

                card_cls = "proposal-card"
                if pstatus == "accepted":
                    card_cls += " proposal-accepted"
                elif pstatus == "rejected":
                    card_cls += " proposal-rejected"
                elif pstatus == "expired":
                    card_cls += " proposal-expired"

                st.markdown(
                    '<div class="{cls}">'
                    '<strong>{name}</strong> ({role}) — {badge}<br>'
                    '📅 {date} | ⏰ {start}–{end}'
                    '{note}'
                    '</div>'.format(
                        cls=card_cls, name=pname, role=prole,
                        badge=proposal_status_badge(pstatus),
                        date=pdate, start=str(pstart)[:5], end=str(pend)[:5],
                        note="<br>📝 {}".format(pnote) if pnote else ""
                    ),
                    unsafe_allow_html=True
                )

                if pstatus == "pending":
                    resp_note = st.text_input(t["response_note"], key="mg_resp_{}".format(pid))
                    acol1, acol2, acol3 = st.columns(3)
                    with acol1:
                        if st.button(t["accept"], key="mg_acc_{}".format(pid), use_container_width=True):
                            update_proposal(pid, "accepted", resp_note, "admin")
                            st.success(t["proposal_accepted"])
                            st.rerun()
                    with acol2:
                        if st.button(t["confirm_from_proposal"], key="mg_cfp_{}".format(pid), use_container_width=True):
                            update_proposal(pid, "accepted", resp_note, "admin")
                            expire_other_proposals(sel_code, pid)
                            confirm_meeting_slot(sel_code, pdate, pstart, pend)
                            st.success(t["confirmed"])
                            st.rerun()
                    with acol3:
                        if st.button(t["reject"], key="mg_rej_{}".format(pid), use_container_width=True):
                            update_proposal(pid, "rejected", resp_note, "admin")
                            st.warning(t["proposal_rejected"])
                            st.rerun()

        # İşlemler
        divider()
        st.markdown('<div class="section-head">🔧 {}</div>'.format(t["actions"]), unsafe_allow_html=True)

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

        # Video link
        divider()
        st.markdown('<div class="section-head">🔗 Update Video Link</div>', unsafe_allow_html=True)
        new_vl = st.text_input(t["meeting_video_link"], value=meeting[7] or "", key="mg_vl")
        if st.button(t["update_link"], key="mg_upd"):
            update_meeting_link(sel_code, new_vl)
            st.success(t["link_updated"])
            st.rerun()

        # Geçmiş
        divider()
        st.markdown('<div class="section-head">{}</div>'.format(t["history"]), unsafe_allow_html=True)
        hist = get_meeting_history(sel_code)
        if hist:
            for h in hist:
                st.markdown(
                    '<div class="history-item"><strong>{action}</strong> — {detail}<br>'
                    '<small style="color:#94a3b8">{ts}</small></div>'.format(
                        action=h[0], detail=h[1], ts=h[2]
                    ),
                    unsafe_allow_html=True
                )
        else:
            empty_state(t["no_history"])
        card_close()
