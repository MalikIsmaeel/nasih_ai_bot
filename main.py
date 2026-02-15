import telebot
import requests
import json

TELEGRAM_TOKEN = "8563422388:AAGNMKKbmoR-JvgFxj6SNhVHW1HA80PFcjA"
OLLAMA_URL = "http://localhost:11434/api/chat"
bot = telebot.TeleBot(TELEGRAM_TOKEN)

user_context = {}

def safe_for_ai(text):
    blocked = ['سكس', 'xxx', 'إباحيات', 'نيك']
    return not any(word in text.lower() for word in blocked)

@bot.message_handler(commands=['/start'])
def start_message(message):
    user_context[message.chat.id] = {'custom_prompt': None}
    bot.reply_to(message, "🤖 **ناصِح AI** | سرعة + خصوصية\n\n`/prompt` `/reset` `/status`", parse_mode='Markdown')

@bot.message_handler(commands=['prompt'])
def set_prompt(message):
    chat_id = message.chat.id
    msg = bot.reply_to(message, "✍️ **الـ prompt الجديد:**", parse_mode='Markdown')
    user_context[chat_id] = user_context.get(chat_id, {})
    user_context[chat_id]['waiting_prompt'] = True
    user_context[chat_id]['prompt_message_id'] = msg.message_id

@bot.message_handler(commands=['reset'])
def reset_context(message):
    chat_id = message.chat.id
    user_context[chat_id] = {'custom_prompt': None}
    bot.reply_to(message, "🔄 **ريستارت!** جاهز 🚀", parse_mode='Markdown')

@bot.message_handler(commands=['status'])
def show_status(message):
    chat_id = message.chat.id
    context = user_context.get(chat_id, {})
    status = "✅ مخصص" if context.get('custom_prompt') else "📋 افتراضي"
    bot.reply_to(message, f"📊 **الحالة:** {status}\n💡 `/prompt`", parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text.strip()
    
    context = user_context.get(chat_id, {})
    if context.get('waiting_prompt'):
        user_context[chat_id]['custom_prompt'] = text
        user_context[chat_id]['waiting_prompt'] = False
        bot.edit_message_text(f"✅ **تم الحفظ!**\n📝 *{text[:70]}...*", 
                            chat_id, context['prompt_message_id'], parse_mode='Markdown')
        return
    
    if not safe_for_ai(text):
        bot.reply_to(message, "🔒 **غير مناسب**", parse_mode='Markdown')
        return
    
    loading_msg = bot.reply_to(message, "🧠 **يحلل...** ⏳")
    
    # PROMPT قوي يفرض الهيكل بالضبط
    base_prompt = context.get('custom_prompt') or """```
أنت ناصِح مالي سعودي. أجب بهذا الهيكل بالضبط:

🧠 **ناصِح | [الموضوع]**
✅ **فهمتك:** [تلخيص واحد]
💰 **أقل سعر:** [المبلغ + العملة]
💡 **خطة (3 خطوات):**
1️⃣ [خطوة واضحة]
2️⃣ [خطوة واضحة]
3️⃣ [خطوة واضحة]
❓ **سؤالي:** [سؤال واحد]

**إجباري:**
- لا تكتب شيء قبل أو بعد الهيكل
- استخدم الإيموجي المحدد
- رد قصير جداً
- أرقام سعودية 2026
```"""
    
    payload = {
        "model": "llama3.2:1b",
        "messages": [
            {"role": "system", "content": base_prompt},
            {"role": "user", "content": text}
        ],
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 300}
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=25)
        response.raise_for_status()
        
        ai_reply = response.json()['message']['content'].strip()
        final_reply = f"🤖 **ناصِح AI:**\n\n{ai_reply}"
        
        bot.edit_message_text(final_reply, chat_id, loading_msg.message_id, parse_mode='Markdown')
        
    except Exception:
        bot.edit_message_text("❌ **خطأ:**\n-  ollama serve\n-  ollama pull llama3.2:1b", 
                            chat_id, loading_msg.message_id, parse_mode='Markdown')

if __name__ == "__main__":
    print("🚀 ناصِح AI | جاهز!")
    bot.infinity_polling()
