import openai
import os

# OpenRouter API Anahtarını Çevre Değişkeninden Al
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Eğer çevre değişkeni yoksa, hata ver (opsiyonel)
if not OPENROUTER_API_KEY:
    raise ValueError("OpenRouter API key is not set. Please set the 'OPENROUTER_API_KEY' environment variable.")

# OpenAI istemcisine OpenRouter temel URL'sini (base URL) ve API Anahtarını tanıt
openai.api_key = OPENROUTER_API_KEY
openai.api_base = "https://openrouter.ai/api/v1"

# Model adını tanımlayın (OpenRouter üzerinden kullanılacak model)
MODEL_NAME = "openai/gpt-4o"  # OpenRouter üzerindeki GPT-4o model ismi

def generate_meeting_email(meeting_title, matches, language="English"):
    """
    Toplantı başlığı ve eşleşen zaman dilimlerine göre OpenRouter GPT-4o üzerinden profesyonel bir toplantı davet e-postası oluşturur.
    """
    # Eşleşen zaman dilimlerini metne dönüştür
    match_text = "\n".join(
        [f"- Date: {m['Date']}, From: {m['Available From']}, Until: {m['Available Until']}"
         for m in matches]
    )

    # GPT-4o için prompt hazırlığı (dil seçimi opsiyonel)
    if language == "English":
        prompt = f"""
        Generate a professional meeting invitation email.
        Meeting Title: {meeting_title}
        Matching Time Slots:
        {match_text}

        The email should briefly summarize the matched time slots and encourage participants to confirm the preferred time slot.
        Include a polite and professional closing.
        """
    elif language == "Türkçe":
        prompt = f"""
        Lütfen aşağıdaki bilgileri içeren profesyonel bir toplantı davet e-postası oluştur.
        Toplantı Başlığı: {meeting_title}
        Eşleşen Zaman Dilimleri:
        {match_text}

        E-posta, eşleşen zaman dilimlerini özetlemeli ve katılımcılardan tercih ettikleri zaman dilimini onaylamalarını rica etmelidir.
        Kibar ve profesyonel bir kapanış ekleyiniz.
        """

    # OpenRouter API üzerinden GPT-4o modeline istek gönder
    response = openai.ChatCompletion.create(
        model=MODEL_NAME,  # OpenRouter üzerinden GPT-4o modelini kullanıyoruz
        messages=[
            {"role": "system", "content": "You are a helpful assistant that writes professional emails."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=400,
        temperature=0.7
    )

    # Yanıtı al ve temizle
    email_body = response["choices"][0]["message"]["content"].strip()
    return email_body


def ai_chatbot_response(message, language="English"):
    """
    Kullanıcının mesajına OpenRouter API üzerinden GPT-4o modeli ile yanıt veren AI Chatbot fonksiyonu.
    """
    # Sistem mesajını dil seçimine göre ayarla
    if language == "English":
        system_message = "You are a friendly, helpful assistant that answers questions about meeting scheduling."
    elif language == "Türkçe":
        system_message = "Sen toplantı planlama konusunda yardımcı olan, dostça ve bilgili bir asistansın."

    # Kullanıcı mesajını OpenRouter API üzerinden GPT-4o modeline gönder
    response = openai.ChatCompletion.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": message}
        ],
        max_tokens=300,
        temperature=0.7
    )

    # Yanıtı al ve temizle
    bot_reply = response["choices"][0]["message"]["content"].strip()
    return bot_reply
