import telebot
import requests
import json
from datetime import datetime

TELEGRAM_TOKEN = "8563422388:AAGNMKKbmoR-JvgFxj6SNhVHW1HA80PFcjA"
OLLAMA_URL = "http://localhost:11434/api/chat"
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# كلمات حساسة
SENSITIVE_WORDS = ['جنس', 'سكس', 'إباحي', 'xxx']

# ذاكرة المستخدم
user_context = {}

# ============================
# 1) رسالة البداية
# ============================
@bot.message_handler(commands=['start'])
def start_message(message):
    user_context[message.chat.id] = {'custom_prompt': None}
    bot.reply_to(message, """
🤖 **ناصِح AI | مساعد ذكي**

✨ *مميزات النسخة الذكية:*
• تحكم كامل في الـ Prompt  
• ردود أسرع وأكثر دقة  
• فلترة ذكية للمحتوى  
• خصوصية 100% (Localhost)

**الأوامر:**
`/prompt` — ضبط الـ Prompt  
`/reset` — إعادة التهيئة  
`/status` — حالة البوت

جرّب: *عاوز جهاز عرس بـ 15 ألف*
    """, parse_mode='Markdown')

# ============================
# 2) ضبط الـ Prompt
# ============================
@bot.message_handler(commands=['prompt'])
def set_prompt(message):
    chat_id = message.chat.id
    bot.reply_to(message, "✍️ **اكتب الـ Prompt الجديد:**", parse_mode='Markdown')
    user_context[chat_id]['waiting_prompt'] = True

# ============================
# 3) إعادة التهيئة
# ============================
@bot.message_handler(commands=['reset'])
def reset_context(message):
    chat_id = message.chat.id
    user_context[chat_id] = {'custom_prompt': None}
    bot.reply_to(message, "🔄 **تمت إعادة التهيئة!**")

# ============================
# 4) حالة البوت
# ============================
@bot.message_handler(commands=['status'])
def show_status(message):
    chat_id = message.chat.id
    prompt_status = "مخصص" if user_context.get(chat_id, {}).get('custom_prompt') else "افتراضي"
    bot.reply_to(message, f"""
📊 **حالة البوت:**
• الـ Prompt: {prompt_status}
• النموذج: llama3.2:1b
    """, parse_mode='Markdown')

# ============================
# 5) المعالجة الأساسية
# ============================
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text.strip()

    # استقبال الـ Prompt الجديد
    if user_context.get(chat_id, {}).get('waiting_prompt'):
        user_context[chat_id]['custom_prompt'] = text
        user_context[chat_id]['waiting_prompt'] = False
        bot.reply_to(message, "✅ **تم حفظ الـ Prompt الجديد!**")
        return

    # فلترة المحتوى الحساس
    if any(word in text for word in SENSITIVE_WORDS):
        bot.reply_to(message, "🚫 **الموضوع غير مسموح**")
        return

    # رسالة تحميل
    loading = bot.reply_to(message, "🧠 **جاري التحليل...**")

    # الـ Prompt الأساسي
    base_prompt = user_context.get(chat_id, {}).get('custom_prompt')
    if not base_prompt:
        base_prompt = """
أنت ناصح مالي سعودي. رد دائمًا بهذا الشكل:

🧠 **ناصِح | [الموضوع]**
✅ **فهمتك:** [ملخص]
💰 **أقل سعر:** [رقم]
💡 **خطة (3 خطوات):**
1️⃣ خطوة  
2️⃣ خطوة  
3️⃣ خطوة  
❓ **سؤالي:** سؤال واحد

شروط:
- الرد 6 أسطر فقط
- أرقام + إيموجي
- حلول سعودية 2026
        """

    # إعداد الطلب
    payload = {
        "model": "llama3.2:1b",
        "messages": [
            {"role": "system", "content": base_prompt},
            {"role": "user", "content": text}
        ],
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.9,
            "num_predict": 200
        }
    }

    # إرسال الطلب
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=25)
        ai_reply = response.json()['message']['content'].strip()

        bot.edit_message_text(
            f"🤖 **ناصِح AI:**\n\n{ai_reply}",
            chat_id,
            loading.message_id,
            parse_mode='Markdown'
        )

    except Exception:
        bot.edit_message_text(
            "❌ **خطأ في الاتصال بـ Ollama**\nتأكد أن السيرفر شغال.",
            chat_id,
            loading.message_id
        )

# ============================
# تشغيل البوت
# ============================
if __name__ == "__main__":
    print("🚀 ناصِح AI جاهز!")
    bot.infinity_polling()
