import telebot
import requests
import re
import json
import os
from datetime import datetime

# استدعاء ملف تحليل الشخصية
from personality import analyze_personality

TELEGRAM_TOKEN = "8563422388:AAGNMKKbmoR-JvgFxj6SNhVHW1HA80PFcjA"
OLLAMA_URL = "http://localhost:11434/api/chat"

bot = telebot.TeleBot(TELEGRAM_TOKEN, skip_pending=True)

SENSITIVE_WORDS = ['جنس', 'سكس', 'إباحي', 'xxx']

DATA_DIR = "data"
LOG_FILE = "bot_logs.txt"

os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------------------------------------
# Logging to TXT
# ---------------------------------------------------------

def log_event(text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {text}\n")

# ---------------------------------------------------------
# JSON Memory System
# ---------------------------------------------------------

def save_user_data(chat_id, data):
    file_path = f"{DATA_DIR}/{chat_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    log_event(f"تم تحديث ملف JSON للمستخدم {chat_id}")

def load_user_data(chat_id):
    file_path = f"{DATA_DIR}/{chat_id}.json"

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    # إصلاح تلقائي للحقول الناقصة
    data.setdefault("custom_prompt", None)
    data.setdefault("keywords", [])
    data.setdefault("history", [])
    data.setdefault("analysis_memory", [])
    data.setdefault("paths", [])
    data.setdefault("best_path", None)

    data.setdefault("personality_profile", {
        "traits": [],
        "communication_style": "",
        "interests": [],
        "strengths": [],
        "weaknesses": [],
        "last_update": ""
    })

    return data

# ---------------------------------------------------------
# A* Inspired Path Builder
# ---------------------------------------------------------

def build_path(keywords, history):
    if not keywords:
        return None

    path = {
        "nodes": keywords[-5:],
        "context": history[-1] if history else "",
        "score": len(keywords[-5:]),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return path

def choose_best_path(paths):
    if not paths:
        return None
    return sorted(paths, key=lambda p: p["score"], reverse=True)[0]

# ---------------------------------------------------------
# Ollama Request
# ---------------------------------------------------------

def ask_ollama(messages, model="qwen2.5:1.5b", retries=3, timeout=45):
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.5,
            "num_predict": 500,
            "top_p": 0.9
        }
    }

    for attempt in range(retries):
        try:
            log_event(f"محاولة {attempt+1} لإرسال الطلب إلى Ollama")
            response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)

            if response.status_code == 200:
                log_event("Ollama ردّ بنجاح")
                return response.json()["message"]["content"].strip()

        except Exception as e:
            log_event(f"خطأ أثناء الاتصال بـ Ollama: {e}")

    log_event("فشل الاتصال بـ Ollama بعد كل المحاولات")
    return None

# ---------------------------------------------------------
# Main Handler
# ---------------------------------------------------------

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text.strip()

    data = load_user_data(chat_id)

    # Sensitive filter
    if any(word in text.lower() for word in SENSITIVE_WORDS):
        bot.reply_to(message, "🚫 **الموضوع غير مسموح**")
        return

    log_event(f"رسالة جديدة من المستخدم {chat_id}: {text}")

    # تحليل الشخصية (من الملف الخارجي)
    data["personality_profile"] = analyze_personality(text, data["personality_profile"])

    # استخراج كلمات مفتاحية
    extracted = re.findall(r'\b\w+\b', text)
    extracted = [w for w in extracted if len(w) > 3]

    if extracted:
        log_event(f"كلمات مفتاحية جديدة: {extracted}")
        data['keywords'].extend(extracted)

    # حفظ آخر 5 رسائل
    data['history'].append(text)
    data['history'] = data['history'][-5:]

    # بناء مسار جديد
    new_path = build_path(data['keywords'], data['history'])
    if new_path:
        data['paths'].append(new_path)
        log_event(f"مسار جديد: {new_path}")

    # اختيار أفضل مسار
    data['best_path'] = choose_best_path(data['paths'])
    log_event(f"أفضل مسار: {data['best_path']}")

    save_user_data(chat_id, data)

    # رسالة "يفكر"
    loading_msg = bot.reply_to(message, "🧠 **يفكر بسرعة...** ⏳")

    # ---------------------------------------------------------
    # Build Prompt
    # ---------------------------------------------------------

    base_prompt = f"""
أنت معين شخصي سريع التحليل.

تحليل شخصية المستخدم:
السمات: {data['personality_profile']['traits']}
نقاط القوة: {data['personality_profile']['strengths']}
نقاط الضعف: {data['personality_profile']['weaknesses']}
الاهتمامات: {data['personality_profile']['interests']}
أسلوب التواصل المفضل: {data['personality_profile']['communication_style']}
آخر تحديث: {data['personality_profile']['last_update']}

أفضل مسار (Best Path):
{data['best_path']}

الكلمات المفتاحية:
{', '.join(data['keywords'])}

آخر الرسائل:
{data['history']}

دورك:
- تحليل سريع
- سؤال واحد فقط إن لزم
- ثم تقديم الحل مباشرة
- بدون نقاش طويل
"""

    # ---------------------------------------------------------
    # Send to Ollama
    # ---------------------------------------------------------

    ai_reply = ask_ollama(
        [
            {"role": "system", "content": base_prompt},
            {"role": "user", "content": text}
        ]
    )

    if not ai_reply:
        bot.edit_message_text("❌ **تعذّر الاتصال بـ Ollama**", chat_id, loading_msg.message_id)
        return

    bot.edit_message_text(f"🤖 **معينك الشخصي:**\n\n{ai_reply}", chat_id, loading_msg.message_id)

# ---------------------------------------------------------
# Run Bot
# ---------------------------------------------------------

if __name__ == "__main__":
    log_event("🚀 تشغيل البوت")
    bot.infinity_polling(skip_pending=True)
