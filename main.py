import telebot
import requests
import json
from datetime import datetime
import re

TELEGRAM_TOKEN = "8563422388:AAGNMKKbmoR-JvgFxj6SNhVHW1HA80PFcjA"
OLLAMA_URL = "http://localhost:11434/api/chat"
bot = telebot.TeleBot(TELEGRAM_TOKEN)

SENSITIVE_WORDS = ['جنس', 'سكس', 'إباحي', 'xxx']
user_context = {}

@bot.message_handler(commands=['/start'])
def start_message(message):
    user_context[message.chat.id] = {'goal': None, 'custom_prompt': None}
    bot.reply_to(message, """
🤖 **ناصِح AI | بوت ذكي مخصص**  

✅ **المميزات:**
• **أنت** تتحكم في الـ Prompt  
• سرعة 3-5 ثواني  
• خصوصية 100% localhost  

**الأوامر:**
`/prompt` - ضبط الـ prompt الخاص بيك  
`/reset` - ريستارت  
`/status` - حالة البوت  

اختبرني: `عاوز جهاز عرس بـ 15 ألف`
    """, parse_mode='Markdown')

@bot.message_handler(commands=['prompt'])
def set_prompt(message):
    chat_id = message.chat.id
    msg = bot.reply_to(message, "✍️ **اكتب الـ prompt الجديد:**\n\n*ملاحظة: هيشتغل مع الشروط الإجبارية*", parse_mode='Markdown')
    
    user_context[chat_id]['waiting_prompt'] = True
    user_context[chat_id]['prompt_message_id'] = msg.message_id

@bot.message_handler(commands=['reset'])
def reset_context(message):
    chat_id = message.chat.id
    user_context[chat_id] = {'goal': None, 'custom_prompt': None}
    bot.reply_to(message, "🔄 **تم الريستارت!** جاهز لمحادثة جديدة 🚀")

@bot.message_handler(commands=['status'])
def show_status(message):
    chat_id = message.chat.id
    context = user_context.get(chat_id, {})
    prompt_status = "✅ مخصص" if context.get('custom_prompt') else "📋 افتراضي"
    
    bot.reply_to(message, f"""
📊 **حالة البوت:**
• Prompt: {prompt_status}
• نموذج: llama3.2:1b

💡 غيّر الـ prompt بـ `/prompt`
    """, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text.strip()
    
    # التحقق من انتظار الـ prompt
    if chat_id in user_context and user_context[chat_id].get('waiting_prompt'):
        custom_prompt = text
        user_context[chat_id]['custom_prompt'] = custom_prompt
        user_context[chat_id]['waiting_prompt'] = False
        
        bot.edit_message_text(
            f"✅ **تم حفظ الـ Prompt الجديد!**\n\n📝 *{custom_prompt[:100]}...*\n\nجاهز للاستخدام 🚀", 
            chat_id, 
            user_context[chat_id]['prompt_message_id'],
            parse_mode='Markdown'
        )
        return
    
    # فلترة المحتوى الحساس
    if any(word in text.lower() for word in SENSITIVE_WORDS):
        bot.reply_to(message, "🔒 **الموضوع يحتاج متخصص معتمد** 📞\n\n💡 جرب: `/prompt` لتخصيص")
        return
    
    # رسالة التحميل
    loading_msg = bot.reply_to(message, "🧠 **ناصِح بيحلل...** ⏳")
    
    # إعداد السياق
    if chat_id not in user_context:
        user_context[chat_id] = {}
    
    # الـ Prompt النهائي (مخصص أو افتراضي)
    base_prompt = user_context[chat_id].get('custom_prompt')
    
    if not base_prompt:
        base_prompt = """
أنت ناصح مالي سعودي 🤝. رد دائماً بهيكل ثابت:

🧠 **ناصِح | [الموضوع]**
✅ **فهمتك:** [تلخيص]
💰 **أقل سعر:** [المبلغ]
💡 **خطة (3 خطوات):**
1️⃣ [خطوة 1]
2️⃣ [خطوة 2] 
3️⃣ [خطوة 3]
❓ **سؤالي:** [سؤال واحد]

**شروط إجبارية:**
- رد قصير (6 خطوط)
- أرقام + إيموجي فقط
- حلول سعودية واقعية 2026
        """
    
    # **التغيير الأساسي: إرسال السؤال مباشرة بدون تاريخ المحادثة**
    final_prompt = f"{base_prompt}\n\n**سؤال المستخدم:** {text}"
    
    # طلب Ollama - السؤال مباشرة
    payload = {
        "model": "llama3.2:1b",
        "messages": [
            {"role": "system", "content": base_prompt},
            {"role": "user", "content": text}  # السؤال فقط!
        ],
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 250,
            "top_p": 0.9
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        
        ai_reply = response.json()['message']['content'].strip()
        final_reply = f"🤖 **ناصِح AI:**\n\n{ai_reply}"
        
        bot.edit_message_text(
            final_reply, 
            chat_id, 
            loading_msg.message_id,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        bot.edit_message_text(
            "❌ **خطأ:**\n• `ollama serve` شغال؟\n• `ollama pull llama3.2:1b`؟\n\n`/start` للريستارت", 
            chat_id, 
            loading_msg.message_id,
            parse_mode='Markdown'
        )

if __name__ == "__main__":
    print("🚀 ناصِح AI Bot | السؤال مباشرة للـ AI!")
    print("✅ Terminal 1: ollama serve")
    print("✅ Terminal 2: python bot.py")
    bot.infinity_polling()
