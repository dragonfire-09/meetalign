import os
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def _get_api_key():
    key = os.getenv("OPENROUTER_API_KEY", "")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("OPENROUTER_API_KEY", "")
        except Exception:
            pass
    return key


def _setup():
    key = _get_api_key()
    if key and OPENAI_AVAILABLE:
        openai.api_key = key
        openai.api_base = "https://openrouter.ai/api/v1"
        return True
    return False


def parse_meeting_command(user_message):
    if not _setup():
        return None, "OPENROUTER_API_KEY not set or openai not installed."

    prompt = f"""You are a meeting scheduling assistant. Parse the user message and extract:
- meeting_title (string)
- participant_name (string)
- date (YYYY-MM-DD)
- start_time (HH:MM, 24h)
- end_time (HH:MM, 24h, empty if not given)

Return ONLY valid JSON. No markdown, no explanation.

Example: {{"meeting_title":"EIC Meeting","participant_name":"Moshira","date":"2026-05-12","start_time":"14:00","end_time":""}}

User: {user_message}"""

    try:
        r = openai.ChatCompletion.create(
            model="openai/gpt-4o",
            messages=[
                {"role": "system", "content": "Return only JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.2
        )
        content = r["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        return json.loads(content), None
    except json.JSONDecodeError as e:
        return None, f"AI returned invalid JSON: {e}"
    except Exception as e:
        return None, f"API error: {e}"


def generate_meeting_email(meeting_title, matches, language="English", meeting_link=""):
    if not _setup():
        lines = [f"Meeting: {meeting_title}\n\nMatching slots:"]
        for m in matches:
            lines.append(f"- {m.get('Date','')} | {m.get('Start','')} - {m.get('End','')}")
        if meeting_link:
            lines.append(f"\nMeeting Link: {meeting_link}")
        lines.append("\nPlease confirm your preferred slot.\n\nBest regards,\nMeetAlign")
        return "\n".join(lines)

    match_text = "\n".join(
        [f"- Date: {m.get('Date','')}, Time: {m.get('Start','')} - {m.get('End','')}" for m in matches]
    )

    link_info = f"\nMeeting Link (Zoom/Google Meet): {meeting_link}" if meeting_link else ""

    if language == "Türkçe":
        prompt = f"""Profesyonel bir toplantı davet e-postası yaz.
Toplantı: {meeting_title}
Eşleşen saatler:
{match_text}
{link_info}

Tarih ve saatleri açıkça belirt. Katılımcılardan tercih ettikleri saati onaylamalarını iste.
Kibar ve profesyonel ol. Türkçe yaz."""
    else:
        prompt = f"""Write a professional meeting invitation email.
Meeting: {meeting_title}
Matching time slots:
{match_text}
{link_info}

Clearly state dates and times. Ask participants to confirm their preferred slot.
Be polite and professional."""

    try:
        r = openai.ChatCompletion.create(
            model="openai/gpt-4o",
            messages=[
                {"role": "system", "content": "You write professional meeting invitation emails."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return r["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error: {e}"


def generate_confirmation_email(meeting_title, date, start, end, language="English", meeting_link=""):
    if not _setup():
        link_line = f"\nMeeting Link: {meeting_link}" if meeting_link else ""
        return f"""Hello,

The meeting has been confirmed.

Meeting: {meeting_title}
Date: {date}
Time: {start} - {end}{link_line}

Best regards,
MeetAlign"""

    link_info = f"\nMeeting Link (Zoom/Google Meet): {meeting_link}" if meeting_link else ""

    if language == "Türkçe":
        prompt = f"""Profesyonel bir toplantı onay e-postası yaz.
Toplantı: {meeting_title}
Tarih: {date}
Saat: {start} - {end}
{link_info}

Tarih, saat ve toplantı linkini açıkça belirt. Kibar ve profesyonel ol. Türkçe yaz."""
    else:
        prompt = f"""Write a professional meeting confirmation email.
Meeting: {meeting_title}
Date: {date}
Time: {start} - {end}
{link_info}

Clearly state the date, time and meeting link. Be polite and professional."""

    try:
        r = openai.ChatCompletion.create(
            model="openai/gpt-4o",
            messages=[
                {"role": "system", "content": "You write professional meeting confirmation emails."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.7
        )
        return r["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error: {e}"


def ai_chatbot_response(message, language="English"):
    if not _setup():
        return "AI not available. Check OPENROUTER_API_KEY."

    sys_msg = ("Sen toplantı planlama konusunda yardımcı olan dostça bir asistansın. Türkçe yanıt ver."
               if language == "Türkçe"
               else "You are a friendly assistant that helps with meeting scheduling.")

    try:
        r = openai.ChatCompletion.create(
            model="openai/gpt-4o",
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": message}
            ],
            max_tokens=400,
            temperature=0.7
        )
        return r["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error: {e}"
