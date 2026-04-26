import openai
import os

# OpenAI API anahtarını çevre değişkeninden al
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_meeting_email(meeting_title, matches):
    """
    GPT-4o kullanarak profesyonel bir toplantı davet e-postası oluşturur.
    meeting_title: Toplantı başlığı
    matches: Eşleşen zaman dilimleri listesi, her biri {Date, Available From, Available Until} formatında
    """
    # Eşleşen zaman dilimlerini metne dönüştürme
    match_text = "\n".join(
        [f"- Date: {m['Date']}, From: {m['Available From']}, Until: {m['Available Until']}"
         for m in matches]
    )

    # GPT-4o için prompt hazırlığı
    prompt = f"""
    Generate a professional meeting invitation email.
    Meeting Title: {meeting_title}
    Matching Time Slots:
    {match_text}
    
    The email should briefly summarize the matched time slots and encourage participants to confirm the preferred time slot.
    Include a polite and professional closing.
    """

    # GPT-4o modeline istek gönderme
    response = openai.ChatCompletion.create(
        model="gpt-4o",  # GPT-4o modelini kullanıyoruz
        messages=[
            {"role": "system", "content": "You are a helpful assistant that writes professional emails."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300
    )

    # Yanıtı al ve temizle
    email_body = response["choices"][0]["message"]["content"].strip()
    return email_body


def ai_chatbot_response(message, language="English"):
    """
    GPT-4o tabanlı basit bir AI chatbot cevabı döndürür.
    message: Kullanıcının mesajı
    language: Kullanılan dil (Varsayılan: İngilizce)
    """
    if language == "English":
        system_message = "You are a friendly, helpful assistant that answers questions about meeting scheduling."
    elif language == "Türkçe":
        system_message = "Sen toplantı planlama konusunda yardımcı olan, dostça ve bilgili bir asistansın."

    # GPT-4o modeline mesaj gönderme
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": message}
        ],
        max_tokens=200
    )

    # Yanıtı al ve temizle
    bot_reply = response["choices"][0]["message"]["content"].strip()
    return bot_reply
