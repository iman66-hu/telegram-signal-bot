import requests

BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "8430812593"

text = """✅ ربات با موفقیت فعال شد

🚀 BUY TEST
⏰ TimeFrame: 15m
"""

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

response = requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": text
    }
)

print(response.text)
