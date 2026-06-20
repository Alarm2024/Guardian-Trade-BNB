import os
import requests
import time
from google import genai

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

API_KEY = os.environ.get("GEMINI_API_KEY")
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY")

client = genai.Client(api_key=API_KEY) if API_KEY else None

def send_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
    except:
        pass

def ask_model(text):
    if DEEPSEEK_KEY:
        try:
            response = requests.post("https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"},
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": text}]}, timeout=30)
            if response.status_code == 402: return "خطأ: رصيد DeepSeek غير كافٍ (402)."
            return response.json()['choices'][0]['message']['content']
        except Exception as e: return f"Error: {str(e)}"
    elif client:
        try:
            response = client.models.generate_content(model='gemini-2.5-flash', contents=text)
            return response.text
        except Exception as e:
            if "429" in str(e): return "خطأ: لقد تجاوزت حد الحصة المجانية (Quota). يرجى الانتظار أو الشحن."
            return f"Error: {str(e)}"
    return "No API configured."

offset = 0
print("--- Pro Guardian Bot Active ---")

while True:
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}"
        updates = requests.get(url, timeout=10).json()
        if "result" in updates:
            for update in updates["result"]:
                offset = update["update_id"] + 1
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    user_text = update["message"]["text"]
                    send_message(chat_id, ask_model(user_text))
    except:
        pass
    time.sleep(2)
