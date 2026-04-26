import requests
import streamlit as st


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def generate_meeting_email(meeting_title, matches):
    api_key = st.secrets.get("OPENROUTER_API_KEY", None)

    if not api_key:
        return "OpenRouter API key is missing. Please add OPENROUTER_API_KEY to Streamlit Secrets."

    if not matches:
        return "No matching time slots found yet. Please add availability first."

    match_text = "\n".join(
        [
            f"- {m['Date']} from {m['Available From']} to {m['Available Until']}"
            for m in matches
        ]
    )

    prompt = f"""
Write a concise, professional email in English.

Context:
The user wants to propose meeting times for this meeting:
{meeting_title}

Available matching time slots:
{match_text}

Tone:
Professional, warm, suitable for academic or EU project collaboration.

Output:
Only the email body. Do not include subject line.
"""

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
                "content": "You are a professional email assistant for academic and EU project collaboration meetings."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.4
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            return f"OpenRouter error: {response.status_code} - {response.text}"

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"AI email generation failed: {e}"
