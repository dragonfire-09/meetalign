import json
import requests
import streamlit as st

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_openrouter(prompt, system_message):
    api_key = st.secrets.get("OPENROUTER_API_KEY", None)

    if not api_key:
        return None, "OpenRouter API key is missing."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://meetalign.streamlit.app",
        "X-Title": "MeetAlign"
    }

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.25
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            return None, f"OpenRouter error: {response.status_code} - {response.text}"

        data = response.json()
        return data["choices"][0]["message"]["content"], None

    except Exception as e:
        return None, f"AI request failed: {e}"


def parse_meeting_command(user_message):
    prompt = f"""
Extract meeting planning information from the user's message.

User message:
{user_message}

Return ONLY valid JSON:
{{
  "meeting_title": "",
  "participant_name": "",
  "participant_email": "",
  "date": "",
  "start_time": "",
  "end_time": "",
  "duration_minutes": 30,
  "notes": ""
}}

Rules:
- Understand Turkish and English.
- Date format must be YYYY-MM-DD.
- Time format must be HH:MM.
- If only start_time is given, set end_time by adding 30 minutes.
- If date is missing or ambiguous, leave date empty.
- Return only JSON, no markdown.
"""

    result, error = call_openrouter(
        prompt,
        "You extract structured meeting data from Turkish or English scheduling instructions. Return only valid JSON."
    )

    if error:
        return None, error

    cleaned = result.strip().replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(cleaned), None
    except Exception:
        return None, f"AI could not return valid JSON. Raw response: {result}"


def generate_invitation_email(
    meeting_title,
    meeting_link,
    meeting_code,
    participant_name="",
    date="",
    start_time="",
    end_time=""
):
    date_line = ""
    if date and start_time and end_time:
        date_line = f"""
Proposed organizer availability:
Date: {date}
Time: {start_time} - {end_time}
"""

    prompt = f"""
Write a concise, professional meeting availability invitation email.

Meeting title:
{meeting_title}

Participant name:
{participant_name}

Meeting link:
{meeting_link}

Meeting code:
{meeting_code}

{date_line}

Important:
- Mention the proposed date/time if provided.
- Ask the recipient to add their availability using the link.
- Keep it warm, professional and suitable for academic / EU project collaboration.
- Output only email body.
"""

    result, error = call_openrouter(
        prompt,
        "You write professional scheduling emails for research and EU project collaboration."
    )

    return error if error else result


def generate_meeting_email(
    meeting_title,
    date,
    start_time,
    end_time,
    participant_name="",
    meeting_link="",
    google_meet_note="Coming Soon"
):
    prompt = f"""
Write a concise professional meeting confirmation email.

Meeting title:
{meeting_title}

Participant:
{participant_name}

Confirmed date:
{date}

Confirmed time:
{start_time} - {end_time}

Meeting link:
{meeting_link}

Google Meet:
{google_meet_note}

Important:
- Clearly state the confirmed date and time.
- Mention that Google Meet connection is coming soon if no Meet link exists.
- Output only email body.
"""

    result, error = call_openrouter(
        prompt,
        "You write professional meeting confirmation emails."
    )

    return error if error else result
