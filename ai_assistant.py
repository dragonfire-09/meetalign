import json
import requests
import streamlit as st


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_openrouter(prompt, system_message):
    api_key = st.secrets.get("OPENROUTER_API_KEY", None)

    if not api_key:
        return None, "OpenRouter API key is missing. Please add OPENROUTER_API_KEY to Streamlit Secrets."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://meetalign.streamlit.app",
        "X-Title": "MeetAlign"
    }

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2
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

Return ONLY valid JSON with this exact structure:
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
- Understand both Turkish and English.
- If the user does not provide a field, use an empty string.
- Date must be YYYY-MM-DD if possible.
- Times must be HH:MM if possible.
- If only a start time is given and no duration is clear, use 30 minutes and calculate end_time.
- If the user says "yarın", "bugün", "next Monday", or similar relative expressions, infer the most likely date based on context if possible.
- If the date is ambiguous, leave date empty.
- Do not add markdown.
- Do not wrap JSON in code fences.
- Return only valid JSON.
"""

    result, error = call_openrouter(
        prompt,
        "You extract structured meeting data from Turkish or English scheduling instructions. You return only valid JSON."
    )

    if error:
        return None, error

    try:
        return json.loads(result), None
    except Exception:
        cleaned = result.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned.replace("```", "").strip()

        try:
            return json.loads(cleaned), None
        except Exception:
            return None, f"AI could not return valid JSON. Raw response: {result}"


def generate_meeting_email(meeting_title, date, start_time, end_time, participant_name="", meeting_link="", google_meet_note="Coming Soon"):
    prompt = f"""
Write a concise, professional meeting confirmation email in English.

Meeting title:
{meeting_title}

Participant name:
{participant_name}

Date:
{date}

Time:
{start_time} - {end_time}

Meeting availability / confirmation link:
{meeting_link}

Google Meet:
{google_meet_note}

Tone:
Professional, warm, suitable for academic, research, or EU project collaboration.

Output:
Only the email body. Do not include subject line.
"""

    result, error = call_openrouter(
        prompt,
        "You are a professional email assistant for academic and EU project collaboration meetings."
    )

    if error:
        return error

    return result


def generate_invitation_email(meeting_title, meeting_link, meeting_code, participant_name=""):
    prompt = f"""
Write a concise, professional meeting availability invitation email in English.

Meeting title:
{meeting_title}

Participant name:
{participant_name}

Meeting link:
{meeting_link}

Meeting code:
{meeting_code}

Purpose:
Ask the recipient to add their availability using the link.

Tone:
Professional, warm, suitable for academic, research, startup, or EU project collaboration.

Output:
Only the email body. Do not include subject line.
"""

    result, error = call_openrouter(
        prompt,
        "You are a professional email assistant for scheduling research and project collaboration meetings."
    )

    if error:
        return error

    return result
