import json
import os
from datetime import datetime, timedelta


def _get_client():
    try:
        import streamlit as st
        api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
        if not api_key:
            return None
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except Exception:
        return None


def _chat(system_msg, user_msg, max_tokens=1000):
    client = _get_client()
    if not client:
        return None
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return r.choices[0].message.content.strip()
    except Exception:
        return None


# ═══════════════════════════════════════════════════════
# PARSE MEETING COMMAND
# ═══════════════════════════════════════════════════════
def parse_meeting_command(text):
    system = (
        "You are a meeting scheduling assistant. Parse the user message and extract:\n"
        "- meeting_title (string)\n"
        "- participant_name (string)\n"
        "- date (YYYY-MM-DD format)\n"
        "- start_time (HH:MM format)\n"
        "- end_time (HH:MM format, default 30 min after start if not specified)\n\n"
        "Return ONLY valid JSON. Example:\n"
        '{"meeting_title":"Team Sync","participant_name":"Alice",'
        '"date":"2026-05-12","start_time":"14:00","end_time":"14:30"}'
    )
    result = _chat(system, text, 500)
    if not result:
        return None, "AI service unavailable. Please create meeting manually."
    try:
        if "```" in result:
            result = result.split("```")[1].replace("json", "").strip()
        parsed = json.loads(result)
        return parsed, None
    except Exception:
        return None, "Could not parse AI response: {}".format(result)


# ═══════════════════════════════════════════════════════
# GENERATE MEETING INVITATION EMAIL
# ═══════════════════════════════════════════════════════
def generate_meeting_email(title, matches, language="English", meeting_link=""):
    slots_lines = []
    for m in matches[:5]:
        line = "- {} {}-{} ({} & {})".format(
            m["Date"], m["Start"], m["End"], m["Organizer"], m["Participant"]
        )
        slots_lines.append(line)
    slots_text = "\n".join(slots_lines)

    lang_note = "Write in Turkish." if language == "Türkçe" else "Write in English."

    system = (
        "You are a professional meeting coordinator. {}\n"
        "Write a brief, professional meeting invitation email. "
        "Include all available slots. If a video link is provided, include it."
    ).format(lang_note)

    user = (
        "Meeting: {}\n"
        "Available slots:\n{}\n"
        "Video link: {}\n\n"
        "Write a professional invitation email."
    ).format(title, slots_text, meeting_link or "N/A")

    result = _chat(system, user, 800)
    if result:
        return result

    vl = ""
    if meeting_link:
        vl = "\n🔗 Video: " + meeting_link
    return (
        "Subject: Meeting Invitation — {title}\n\n"
        "Hello,\n\n"
        "You are invited to: {title}\n\n"
        "Available time slots:\n{slots}\n"
        "{vl}\n\n"
        "Please confirm your preferred time slot.\n\n"
        "Best regards,\nMeetAlign"
    ).format(title=title, slots=slots_text, vl=vl)


# ═══════════════════════════════════════════════════════
# GENERATE CONFIRMATION EMAIL
# ═══════════════════════════════════════════════════════
def generate_confirmation_email(title, date, start, end, language="English", meeting_link=""):
    lang_note = "Write in Turkish." if language == "Türkçe" else "Write in English."

    system = "You are a professional meeting coordinator. {} Write a brief confirmation email.".format(lang_note)
    user = "Meeting '{}' confirmed for {} from {} to {}. Video: {}".format(
        title, date, start, end, meeting_link or "N/A"
    )

    result = _chat(system, user, 500)
    if result:
        return result

    vl = ""
    if meeting_link:
        vl = "\n🔗 Video Link: " + meeting_link
    return (
        "Subject: Meeting Confirmed — {title}\n\n"
        "Hello,\n\n"
        "The following meeting has been confirmed:\n\n"
        "📋 Meeting: {title}\n"
        "📅 Date: {date}\n"
        "⏰ Time: {start} – {end}"
        "{vl}\n\n"
        "Please add this to your calendar.\n\n"
        "Best regards,\nMeetAlign"
    ).format(title=title, date=date, start=start, end=end, vl=vl)


# ═══════════════════════════════════════════════════════
# SUGGEST ALTERNATIVE DATES
# ═══════════════════════════════════════════════════════
def suggest_alternative_dates(org_slots, part_slots, meeting_title="", language="English"):
    """
    org_slots / part_slots: [{"Date":"2026-05-10","Start":"09:00","End":"11:00","Name":"..."}]
    Her iki liste de boş olabilir — fallback her zaman çalışır.
    """
    # Boş liste güvenliği
    org_slots = org_slots or []
    part_slots = part_slots or []

    lang_note = "Türkçe yaz." if language == "Türkçe" else "Write in English."

    org_lines = ["- {} {}-{}".format(s["Date"], s["Start"], s["End"]) for s in org_slots]
    org_text = "\n".join(org_lines) if org_lines else "No slots provided"

    part_lines = ["- {} {}-{}".format(s["Date"], s["Start"], s["End"]) for s in part_slots]
    part_text = "\n".join(part_lines) if part_lines else "No slots provided"

    system = (
        "You are a smart meeting scheduling assistant. {}\n"
        "The organizer and participants have no overlapping availability.\n"
        "Analyze both sides and suggest 3 compromise time slots that might work.\n"
        "Consider:\n"
        "1. Dates that are close to both parties available dates\n"
        "2. Times that might require small adjustments from either side\n"
        "3. Common business hours (09:00-18:00)\n\n"
        "Return suggestions as a numbered list with brief reasoning.\n"
        "Also suggest what each party could adjust.\n"
        "Format each suggestion clearly with date and time."
    ).format(lang_note)

    user = (
        "Meeting: {title}\n\n"
        "Organizer available:\n{org}\n\n"
        "Participants available:\n{part}\n\n"
        "No overlap found. Suggest 3 alternative times and explain adjustments needed."
    ).format(title=meeting_title or "Meeting", org=org_text, part=part_text)

    result = _chat(system, user, 900)
    if result:
        return result

    # Fallback: AI yoksa veya hata varsa her zaman çalışan öneriler
    return _fallback_suggestions(org_slots, part_slots, language)


def _fallback_suggestions(org_slots, part_slots, language="English"):
    """AI olmadan çalışan akıllı fallback önerileri."""
    suggestions = []

    # 1. Aynı güne denk gelip saat farkı olan kayıtlar
    same_day_pairs = []
    for o in org_slots:
        for p in part_slots:
            if o.get("Date") == p.get("Date"):
                same_day_pairs.append((o, p))

    for o, p in same_day_pairs[:3]:
        try:
            os_dt = datetime.strptime(str(o["Start"])[:5], "%H:%M")
            oe_dt = datetime.strptime(str(o["End"])[:5], "%H:%M")
            ps_dt = datetime.strptime(str(p["Start"])[:5], "%H:%M")
            pe_dt = datetime.strptime(str(p["End"])[:5], "%H:%M")

            # Org bittikten ne kadar sonra Part başlıyor?
            gap1 = (ps_dt - oe_dt).total_seconds() / 60
            # Part bittikten ne kadar sonra Org başlıyor?
            gap2 = (os_dt - pe_dt).total_seconds() / 60

            if gap1 > 0:
                suggestions.append(
                    "1. {} tarihinde: {} saat bitimine {} dk uzatılırsa veya "
                    "{} saat başlangıcı {} dk öne alınırsa örtüşme sağlanır.".format(
                        o["Date"], o.get("Name", "Organizer"), int(gap1),
                        p.get("Name", "Participant"), int(gap1)
                    ) if language == "Türkçe" else
                    "1. On {}: Organizer ({}) ends at {}, Participant ({}) starts at {} — "
                    "{} min gap. Shift one side by {} min to overlap.".format(
                        o["Date"], o.get("Name", "Org"), o["End"],
                        p.get("Name", "Part"), p["Start"],
                        int(gap1), int(gap1)
                    )
                )
            elif gap2 > 0:
                suggestions.append(
                    "1. {} tarihinde: Katılımcı {} dk erken bitirse örtüşme olur.".format(
                        o["Date"], int(gap2)
                    ) if language == "Türkçe" else
                    "1. On {}: Participant ends at {}, Organizer starts at {} — "
                    "{} min gap. Adjust by {} min.".format(
                        o["Date"], p["End"], o["Start"], int(gap2), int(gap2)
                    )
                )
        except Exception:
            suggestions.append(
                "1. {} tarihinde her iki taraf da uygun — saatleri koordine edin.".format(o["Date"])
                if language == "Türkçe" else
                "1. Both available on {} — coordinate exact times.".format(o["Date"])
            )

    # 2. En yakın tarihleri bul (farklı günler)
    try:
        org_dates = sorted(set(
            datetime.strptime(o["Date"], "%Y-%m-%d") for o in org_slots if o.get("Date")
        ))
        part_dates = sorted(set(
            datetime.strptime(p["Date"], "%Y-%m-%d") for p in part_slots if p.get("Date")
        ))

        close_pairs = []
        for od in org_dates:
            for pd in part_dates:
                diff = abs((od - pd).days)
                if 1 <= diff <= 5:
                    close_pairs.append((diff, od, pd))

        close_pairs.sort()
        for diff, od, pd in close_pairs[:2]:
            mid_date = od + timedelta(days=(pd - od).days // 2)
            n = len(suggestions) + 1
            suggestions.append(
                "{}. {} tarihinde (her iki tarafın mevcut tarihlerine {} gün uzaklıkta) ortak slot deneyin.".format(
                    n, mid_date.strftime("%Y-%m-%d"), diff // 2
                ) if language == "Türkçe" else
                "{}. Try {} (midpoint between organizer's {} and participant's {}, {} day gap).".format(
                    n, mid_date.strftime("%Y-%m-%d"),
                    od.strftime("%Y-%m-%d"), pd.strftime("%Y-%m-%d"), diff
                )
            )
    except Exception:
        pass

    # 3. Genel öneri
    if not suggestions:
        if language == "Türkçe":
            return (
                "🔄 Öneriler:\n\n"
                "1. Her iki taraf da 09:00-10:00 arasında uygunluk eklemeyi deneyebilir.\n"
                "2. Hafta içi öğle saatleri (12:00-13:00) genellikle uyum sağlar.\n"
                "3. Lütfen aşağıdan yeni bir tarih teklif edin."
            )
        return (
            "🔄 Suggestions:\n\n"
            "1. Both parties could try adding availability for 09:00-10:00.\n"
            "2. Midday slots (12:00-13:00) often work for cross-timezone meetings.\n"
            "3. Please propose a new date below."
        )

    header = "🔄 Öneriler:\n\n" if language == "Türkçe" else "🔄 Suggestions:\n\n"
    return header + "\n\n".join(suggestions[:4])


# ═══════════════════════════════════════════════════════
# GENERATE PROPOSAL EMAIL
# ═══════════════════════════════════════════════════════
def generate_proposal_email(title, proposer, date, start, end, language="English", meeting_link=""):
    lang_note = "Türkçe yaz." if language == "Türkçe" else "Write in English."

    system = "You are a meeting coordinator. {} Write a brief email proposing a new meeting time.".format(lang_note)
    user = "{} proposes new time for '{}': {} {}-{}. Video: {}".format(
        proposer, title, date, start, end, meeting_link or "N/A"
    )

    result = _chat(system, user, 400)
    if result:
        return result

    return (
        "Subject: New Time Proposed — {title}\n\n"
        "Hello,\n\n"
        "{proposer} has proposed a new time for the meeting:\n\n"
        "📋 Meeting: {title}\n"
        "📅 Date: {date}\n"
        "⏰ Time: {start} – {end}\n\n"
        "Please review and respond.\n\n"
        "Best regards,\nMeetAlign"
    ).format(title=title, proposer=proposer, date=date, start=start, end=end)


# ═══════════════════════════════════════════════════════
# AI CHATBOT
# ═══════════════════════════════════════════════════════
def ai_chatbot_response(message, language="English"):
    lang_note = "Türkçe yanıt ver." if language == "Türkçe" else "Reply in English."

    system = (
        "You are MeetAlign AI assistant. {}\n"
        "You help with meeting scheduling, time zone questions, "
        "availability coordination, and general productivity.\n"
        "Be concise and helpful."
    ).format(lang_note)

    result = _chat(system, message, 600)
    if result:
        return result

    if language == "Türkçe":
        return "AI servisi şu anda kullanılamıyor. Lütfen daha sonra tekrar deneyin."
    return "AI service is currently unavailable. Please try again later."
