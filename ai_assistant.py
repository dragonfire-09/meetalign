import json
import os
from datetime import datetime, timedelta

def _get_client():
    """Try to get OpenAI client, return None if not available."""
    try:
        import streamlit as st
        api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
        if not api_key:
            return None
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except:
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
    except Exception as e:
        return None

# ═══════════════════════════════════════════════════════
# PARSE MEETING COMMAND
# ═══════════════════════════════════════════════════════
def parse_meeting_command(text):
    system = """You are a meeting scheduling assistant. Parse the user message and extract:
- meeting_title (string)
- participant_name (string)
- date (YYYY-MM-DD format)
- start_time (HH:MM format)
- end_time (HH:MM format, default 30 min after start if not specified)

Return ONLY valid JSON. Example:
{"meeting_title":"Team Sync","participant_name":"Alice","date":"2026-05-12","start_time":"14:00","end_time":"14:30"}
"""
    result = _chat(system, text, 500)
    if not result:
        return None, "AI service unavailable. Please create meeting manually."
    try:
        # Extract JSON from response
        if "```" in result:
            result = result.split("```")[1].replace("json", "").strip()
        parsed = json.loads(result)
        return parsed, None
    except:
        return None, f"Could not parse AI response: {result}"

# ═══════════════════════════════════════════════════════
# GENERATE EMAILS
# ═══════════════════════════════════════════════════════
def generate_meeting_email(title, matches, language="English", meeting_link=""):
    slots_text = "\n".join([f"- {m['Date']} {m['Start']}-{m['End']} ({m['Organizer']} & {m['Participant']})" for m in matches[:5]])
    lang_note = "Write in Turkish." if language == "Türkçe" else "Write in English."

    system = f"""You are a professional meeting coordinator. {lang_note}
Write a brief, professional meeting invitation email. Include all available slots.
If a video link is provided, include it."""

    user = f"""Meeting: {title}
Available slots:
{slots_text}
Video link: {meeting_link or 'N/A'}

Write a professional invitation email."""

    result = _chat(system, user, 800)
    if result:
        return result

    # Fallback
    vl = f"\n🔗 Video: {meeting_link}" if meeting_link else ""
    return f"""Subject: Meeting Invitation — {title}

Hello,

You are invited to: {title}

Available time slots:
{slots_text}
{vl}

Please confirm your preferred time slot.

Best regards,
MeetAlign"""

def generate_confirmation_email(title, date, start, end, language="English", meeting_link=""):
    lang_note = "Write in Turkish." if language == "Türkçe" else "Write in English."

    system = f"You are a professional meeting coordinator. {lang_note} Write a brief confirmation email."
    user = f"Meeting '{title}' confirmed for {date} from {start} to {end}. Video: {meeting_link or 'N/A'}"

    result = _chat(system, user, 500)
    if result:
        return result

    vl = f"\n🔗 Video Link: {meeting_link}" if meeting_link else ""
    return f"""Subject: Meeting Confirmed — {title}

Hello,

The following meeting has been confirmed:

📋 Meeting: {title}
📅 Date: {date}
⏰ Time: {start} – {end}{vl}

Please add this to your calendar.

Best regards,
MeetAlign"""

# ═══════════════════════════════════════════════════════
# SUGGEST ALTERNATIVE DATES (NEW)
# ═══════════════════════════════════════════════════════
def suggest_alternative_dates(org_slots, part_slots, meeting_title="", language="English"):
    """
    When no match found, suggest alternatives.
    org_slots / part_slots: list of dicts with Date, Start, End, Name
    """
    lang_note = "Türkçe yaz." if language == "Türkçe" else "Write in English."

    org_text = "\n".join([f"- {s['Date']} {s['Start']}-{s['End']}" for s in org_slots]) or "No slots"
    part_text = "\n".join([f"- {s['Date']} {s['Start']}-{s['End']}" for s in part_slots]) or "No slots"

    system = f"""You are a smart meeting scheduling assistant. {lang_note}
The organizer and participants have no overlapping availability.
Analyze both sides and suggest 3 compromise time slots that might work.
Consider:
1. Dates that are close to both parties' available dates
2. Times that might require small adjustments from either side
3. Common business hours

Return suggestions as a numbered list with brief reasoning.
Also suggest what each party could adjust."""

    user = f"""Meeting: {meeting_title}

Organizer available:
{org_text}

Participants available:
{part_text}

No overlap found. Suggest 3 alternative times and explain what adjustments would help."""

    result = _chat(system, user, 800)
    if result:
        return result

    # Fallback: algorithmic suggestion
    return _fallback_suggestions(org_slots, part_slots, language)

def _fallback_suggestions(org_slots, part_slots, language="English"):
    """Generate suggestions without AI."""
    suggestions = []

    # Find near-misses: same date, different times
    for o in org_slots:
        for p in part_slots:
            if o["Date"] == p["Date"]:
                suggestions.append(
                    f"📅 {o['Date']}: Organizer {o['Start']}-{o['End']}, "
                    f"Participant {p['Start']}-{p['End']} — Try adjusting times to overlap"
                )

    # Find closest dates
    try:
        org_dates = sorted(set(datetime.strptime(o["Date"], "%Y-%m-%d") for o in org_slots))
        part_dates = sorted(set(datetime.strptime(p["Date"], "%Y-%m-%d") for p in part_slots))

        for od in org_dates:
            for pd in part_dates:
                diff = abs((od - pd).days)
                if 0 < diff <= 3:
                    mid = od + timedelta(days=diff // 2)
                    suggestions.append(
                        f"📅 Suggest {mid.strftime('%Y-%m-%d')}: Between organizer's {od.strftime('%Y-%m-%d')} and participant's {pd.strftime('%Y-%m-%d')}"
                    )
    except:
        pass

    if not suggestions:
        if language == "Türkçe":
            return "❌ Yakın tarih bulunamadı. Lütfen yeni tarihler önerin veya mevcut uygunlukları genişletin."
        return "❌ No close dates found. Please propose new dates or extend your availability windows."

    header = "🔄 Öneriler:" if language == "Türkçe" else "🔄 Suggestions:"
    return header + "\n\n" + "\n".join(suggestions[:5])

# ═══════════════════════════════════════════════════════
# GENERATE PROPOSAL EMAIL (NEW)
# ═══════════════════════════════════════════════════════
def generate_proposal_email(title, proposer, date, start, end, language="English", meeting_link=""):
    lang_note = "Türkçe yaz." if language == "Türkçe" else "Write in English."

    system = f"You are a meeting coordinator. {lang_note} Write a brief email proposing a new meeting time."
    user = f"{proposer} proposes new time for '{title}': {date} {start}-{end}. Video: {meeting_link or 'N/A'}"

    result = _chat(system, user, 400)
    if result:
        return result

    return f"""Subject: New Time Proposed — {title}

Hello,

{proposer} has proposed a new time for the meeting:

📋 Meeting: {title}
📅 Date: {date}
⏰ Time: {start} – {end}

Please review and respond.

Best regards,
MeetAlign"""

# ═══════════════════════════════════════════════════════
# AI CHATBOT
# ═══════════════════════════════════════════════════════
def ai_chatbot_response(message, language="English"):
    lang_note = "Türkçe yanıt ver." if language == "Türkçe" else "Reply in English."

    system = f"""You are MeetAlign AI assistant. {lang_note}
You help with meeting scheduling, time zone questions, availability coordination, and general productivity.
Be concise and helpful."""

    result = _chat(system, message, 600)
    if result:
        return result

    if language == "Türkçe":
        return "AI servisi şu anda kullanılamıyor. Lütfen daha sonra tekrar deneyin."
    return "AI service is currently unavailable. Please try again later."
