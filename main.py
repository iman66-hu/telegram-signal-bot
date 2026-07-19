import requests

BOT_TOKEN ="8848229995:AAHZhAYM-lbNRi8ro_6Ww3vnTHd0i6xtano"
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
