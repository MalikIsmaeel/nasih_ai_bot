import telebot
import requests
import os
from datetime import datetime

# البيانات من Secrets
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
DEEPSEEK_API_KEY = "sk-7cd383e2632e4b558526590fb6ab9314"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

SENSITIVE_WORDS = ['جنس', 'سكس', 'إباحي', 'علاقة خارج', 'مشاكل جنسية']

def deepseek_analyze(prompt):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system", 
                "content": """أنت ناصِح - محلل حياة عربي ذكي. 
                رد بتعاطف + تحليل عميق + خطوات عملية واضحة.
                استخدم لغة بسيطة وعامية + إيموجي مناسبة.
                الرد لا يتجاوز 250 كلمة. ابدأ بتعاطف ثم تحليل ثم حلول.
                لا تكرر نفس الكلام."""
            },
            {"role": "user", "content": f"المشكلة: {prompt}"}
        ],
        "max_tokens": 600,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(DEEPSEEK_URL, json=data, headers=headers, timeout=20)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return "🧠 خذ نفس عميق... أنا معاك، شارك تفاصيل أكثر عشان أساعدك أحسن 🛤️"
    except:
        return "🌐 مشكلة في الاتصال، جرب تاني بعد شوية 🛤️"

@bot.message_handler(commands=['start'])
def start_message(message):
    welcome = """
🧠 **ناصِح | DeepSeek AI** 🛤️

الآن مدعوم بـ **DeepSeek المتطور** 🧠
تحليل أعمق + ذكاء أقوى + نصايح عملية!

💬 شارك مشكلتك الحياتية:
• ضغط عمل 😩
• مشاكل عائلية 👨‍👩‍👧 
• قرارات مهمة ❓
• أي حاجة في الحياة 🌍

**ناصِح معاك لآخر الدرب 🛤️**
    """
    bot.reply_to(message, welcome, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def nasih_deepseek(message):
    text = message.text.lower()
    
    # فلتر المحتوى الحساس
    for word in SENSITIVE_WORDS:
        if word in text:
            response = """
🔒 **موضوع حساس يحتاج خصوصية ومتخصص:**

👨‍⚕️ **أ. محمد الغامدي - استشاري أسري**
⭐ 4.8/5 | 💰 **250 ريال**
⏰ جلسة 45 دقيقة
📲 [احجز الآن wa.me/966501234567]

**ناصِح وجّهك للصح ✅**
            """
            bot.reply_to(message, response, parse_mode='Markdown')
            return
    
    # إرسال لـ DeepSeek
    bot.reply_to(message, "🧠 **ناصِح بيحلل مشكلتك...**")
    analysis = deepseek_analyze(message.text)
    
    response = f"""
🧠 **ناصِح | DeepSeek Analysis** 🛤️

📝 **{analysis}**

**تابع معايا عشان أساعدك أكثر 🛤️**
    """
    bot.reply_to(message, response, parse_mode='Markdown')

print("🚀 ناصِح + DeepSeek شغال 100%! ابحث @nasih_ai_bot")
bot.infinity_polling()