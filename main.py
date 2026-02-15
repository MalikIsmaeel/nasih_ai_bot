import telebot
import requests
import re
import json
import os

TELEGRAM_TOKEN = "8563422388:AAGNMKKbmoR-JvgFxj6SNhVHW1HA80PFcjA"
OLLAMA_URL = "http://localhost:11434/api/chat"

bot = telebot.TeleBot(TELEGRAM_TOKEN, skip_pending=True)

SENSITIVE_WORDS = ['جنس', 'سكس', 'إباحي', 'xxx']

# مجلد تخزين ملفات JSON
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------------------------------------
# دالة حفظ بيانات المستخدم في JSON
# ---------------------------------------------------------

def save_user_data(chat_id, data):
    file_path = f"{DATA_DIR}/{chat_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"[Saved] تم تحديث ملف JSON للمستخدم {chat_id}")

def load_user_data(chat_id):
    file_path = f"{DATA_DIR}/{chat_id}.json"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "custom_prompt": None,
        "keywords": [],
        "history": []
    }

# ---------------------------------------------------------
# دالة محسّنة لإرسال الطلب إلى Ollama
# ---------------------------------------------------------

def ask_ollama(messages, model="qwen2.5:1.5b", retries=3, timeout=45):
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.6,
            "num_predict": 600,
            "top_p": 0.95
        }
    }

    for attempt in range(retries):
        try:
            print(f"[Thinking] محاولة {attempt+1} لإرسال الطلب إلى Ollama...")
            response = requests.post(
                OLLAMA_URL,
                json=payload,
                timeout=timeout
            )

            if response.status_code == 200:
                print("[Success] Ollama ردّ بنجاح")
                return response.json()["message"]["content"].strip()

            if response.status_code >= 500:
                print("[Retry] خطأ من السيرفر… إعادة المحاولة")
                continue

        except Exception as e:
            print(f"[Error] {e} — إعادة المحاولة")

    print("[Fail] فشل الاتصال بـ Ollama بعد كل المحاولات")
    return None


# ---------------------------------------------------------
# أوامر البوت
# ---------------------------------------------------------

@bot.message_handler(commands=['start'])
def start_message(message):
    chat_id = message.chat.id
    data = load_user_data(chat_id)
    save_user_data(chat_id, data)

    bot.reply_to(message, """
🤖 **معينك الشخصي AI | مساعد شامل**

✨ أسلوبي الجديد:
• أناقشك قبل ما أعطي حلول  
• أرتّب الصورة وأوضح الأبعاد  
• أحفظ كلامك كمفاتيح نقاش  
• أبني على إجاباتك السابقة  
• وفي النهاية أعطيك ملخص شامل للحلول  

**الأوامر:**
`/prompt` - تخصيص السلوك  
`/reset` - إعادة التهيئة  
`/status` - حالة البوت
    """, parse_mode='Markdown')


@bot.message_handler(commands=['reset'])
def reset_context(message):
    chat_id = message.chat.id
    data = {
        "custom_prompt": None,
        "keywords": [],
        "history": []
    }
    save_user_data(chat_id, data)
    bot.reply_to(message, "🔄 **تمت إعادة التهيئة بالكامل!**")


@bot.message_handler(commands=['status'])
def show_status(message):
    chat_id = message.chat.id
    data = load_user_data(chat_id)

    prompt_status = "مخصص" if data.get('custom_prompt') else "افتراضي"
    keywords = ", ".join(data.get('keywords', [])) or "لا يوجد بعد"

    bot.reply_to(message, f"""
📊 **حالة البوت:**
• الـ Prompt: {prompt_status}
• الكلمات المفتاحية: {keywords}
• النموذج: qwen2.5:1.5b
    """, parse_mode='Markdown')


@bot.message_handler(commands=['prompt'])
def set_prompt(message):
    chat_id = message.chat.id
    msg = bot.reply_to(message, "✍️ **اكتب الـ prompt الجديد:**", parse_mode='Markdown')

    data = load_user_data(chat_id)
    data['waiting_prompt'] = True
    data['prompt_message_id'] = msg.message_id
    save_user_data(chat_id, data)


# ---------------------------------------------------------
# معالجة الرسائل
# ---------------------------------------------------------

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text.strip()

    data = load_user_data(chat_id)

    # استقبال prompt جديد
    if data.get('waiting_prompt'):
        data['custom_prompt'] = text
        data['waiting_prompt'] = False

        bot.edit_message_text(
            f"✅ **تم حفظ الـ Prompt الجديد!**\n\n📝 *{text[:100]}...*",
            chat_id,
            data['prompt_message_id'],
            parse_mode='Markdown'
        )

        save_user_data(chat_id, data)
        return

    # فلترة المحتوى الحساس
    if any(word in text.lower() for word in SENSITIVE_WORDS):
        bot.reply_to(message, "🚫 **الموضوع غير مسموح**")
        return

    # استخراج كلمات مفتاحية جديدة
    extracted = re.findall(r'\b\w+\b', text)
    extracted = [w for w in extracted if len(w) > 3]

    if extracted:
        print(f"[Learning] كلمات مفتاحية جديدة: {extracted}")
        data['keywords'].extend(extracted)

    # حفظ آخر 5 رسائل
    data['history'].append(text)
    data['history'] = data['history'][-5:]

    save_user_data(chat_id, data)

    # رسالة "يفكر"
    loading_msg = bot.reply_to(message, "🧠 **يفكر معك...** ⏳")
    print(f"[Thinking] المستخدم قال: {text}")

    # ---------------------------------------------------------
    # الـ Prompt الجديد (نظام النقاش)
    # ---------------------------------------------------------

    base_prompt = data.get('custom_prompt')

    if not base_prompt:
        base_prompt = f"""
أنت معين شخصي يعتمد على الحوار العميق وليس الإجابات المباشرة.

دورك:
1) تبدأ دائمًا بتحليل كلام المستخدم وترتيب الصورة.
2) تناقشه وتفتح له زوايا جديدة.
3) تربط بين كلامه الحالي وكلامه السابق.
4) تستخدم الكلمات المفتاحية التالية كمفاتيح نقاش:
{', '.join(data['keywords'])}
5) بعد النقاش، تقدّم ملخصًا شاملًا للحلول الممكنة.

آخر ما قاله المستخدم:
{data['history']}

صيغة الرد:
🧠 **نقاش أوّلي:** تحليل وتوسيع الفكرة  
💬 **تعمّق:** ربط بين النقاط السابقة  
📌 **ملخص الحلول:** نقاط واضحة  
❓ **سؤال جوهري:** سؤال واحد يساعد المستخدم يتقدم
"""

    # ---------------------------------------------------------
    # إرسال الطلب إلى Ollama
    # ---------------------------------------------------------

    ai_reply = ask_ollama(
        [
            {"role": "system", "content": base_prompt},
            {"role": "user", "content": text}
        ]
    )

    if not ai_reply:
        bot.edit_message_text(
            "❌ **تعذّر الاتصال بـ Ollama بعد عدة محاولات**",
            chat_id,
            loading_msg.message_id,
            parse_mode='Markdown'
        )
        return

    bot.edit_message_text(
        f"🤖 **معينك الشخصي:**\n\n{ai_reply}",
        chat_id,
        loading_msg.message_id,
        parse_mode='Markdown'
    )


# ---------------------------------------------------------
# تشغيل البوت
# ---------------------------------------------------------

if __name__ == "__main__":
    print("🚀 معينك الشخصي AI جاهز!")
    bot.infinity_polling(skip_pending=True)
