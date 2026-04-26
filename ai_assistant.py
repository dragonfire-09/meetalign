import os
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def get_client():
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("OPENROUTER_API_KEY", "")
        except Exception:
            pass
    return api_key


def parse_meeting_command(user_message):
    api_key = get_client()

    if not api_key:
        return None, "OPENROUTER_API_KEY is not set in environment or Streamlit Secrets."

    if not OPENAI_AVAILABLE:
        return None, "openai library is not installed. Add 'openai' to requirements.txt."

    openai.api_key = api_key
    openai.api_base = "https://openrouter.ai/api/v1"

    prompt = f"""
You are a meeting scheduling assistant. Parse the user's message and extract:
- meeting_title (string)
- participant_name (string)
- date (YYYY-MM-DD format)
- start_time (HH:MM format, 24h)
- end_time (HH:MM format, 24h, if not given leave empty)

Return ONLY valid JSON, no explanation, no markdown.

Example output:
{{"meeting_title": "EIC Pathfinder Meeting", "participant_name": "Moshira", "date": "2026-05-12", "start_time": "14:00", "end_time": ""}}

User message: {user_message}
"""

    try:
        response = openai.ChatCompletion.create(
            model="openai/gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful meeting scheduling assistant. Return only JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.2
        )

        content = response["choices"][0]["message"]["content"].strip()

        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        parsed = json.loads(content)
        return parsed, None

    except json.JSONDecodeError as e:
        return None, f"AI returned invalid JSON: {e}"
    except Exception as e:
        return None, f"OpenRouter API error: {e}"


def generate_meeting_email(meeting_title, matches, language="English"):
    api_key = get_client()

    if not api_key or not OPENAI_AVAILABLE:
        lines = [f"Meeting: {meeting_title}\n\nMatching slots:"]
        for m in matches:
            lines.append(f"- {m.get('Date', '')} | {m.get('Start', '')} - {m.get('End', '')}")
        lines.append("\nPlease confirm your preferred time slot.\n\nBest regards,\nMeetAlign")
        return "\n".join(lines)

    openai.api_key = api_key
    openai.api_base = "https://openrouter.ai/api/v1"

    match_text = "\n".join(
        [f"- Date: {m.get('Date','')}, From: {m.get('Start','')}, Until: {m.get('End','')}"
         for m in matches]
    )

    if language == "Türkçe":
        prompt = f"""Profesyonel bir toplantı davet e-postası oluştur.
Toplantı: {meeting_title}
Eşleşen saatler:
{match_text}

Katılımcılardan tercih ettikleri saati onaylamalarını iste. Kibar ve profesyonel ol."""
    else:
        prompt = f"""Generate a professional meeting invitation email.
Meeting: {meeting_title}
Matching slots:
{match_text}

Ask participants to confirm their preferred slot. Be polite and professional."""

    try:
        response = openai.ChatCompletion.create(
            model="openai/gpt-4o",
            messages=[
                {"role": "system", "content": "You write professional meeting emails."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.7
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error generating email: {e}"


def ai_chatbot_response(message, language="English"):
    api_key = get_client()

    if not api_key or not OPENAI_AVAILABLE:
        return "AI is not available. Please check OPENROUTER_API_KEY."

    openai.api_key = api_key
    openai.api_base = "https://openrouter.ai/api/v1"

    if language == "Türkçe":
        sys_msg = "Sen toplantı planlama konusunda yardımcı olan dostça bir asistansın. Türkçe yanıt ver."
    else:
        sys_msg = "You are a friendly assistant that helps with meeting scheduling."

    try:
        response = openai.ChatCompletion.create(
            model="openai/gpt-4o",
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": message}
            ],
            max_tokens=300,
            temperature=0.7
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error: {e}"
