import requests
import json

DEEPSEEK_API_KEY = "sk-7cd383e2632e4b558526590fb6ab9314"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "deepseek-chat",
    "messages": [
        {
            "role": "system",
            "content": "أنت مساعد اختبار. رد باختصار."
        },
        {
            "role": "user", 
            "content": "اختبر الـ API: هل شغال؟"
        }
    ],
    "max_tokens": 100
}

print("🧪 Testing DeepSeek API...")
try:
    response = requests.post(DEEPSEEK_URL, headers=headers, json=data, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ API شغال!")
        print("الرد:", result['choices'][0]['message']['content'])
    else:
        print("❌ خطأ:", response.text)
        
except Exception as e:
    print("❌ خطأ اتصال:", str(e))
