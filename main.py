import time
import requests
import pandas as pd
import numpy as np

# ==================== تنظیمات ====================
BOT_TOKEN = "YOUR_BOT_TOKEN"          # توکن جدید بذار
CHAT_ID   = "YOUR_CHAT_ID"            # چت آیدی جدید بذار

INTERVALS = ["5m", "15m", "30m"]
LIMIT = 300

# پارامترهای استراتژی (بهینه‌شده)
RMA_LEN = 120
SMOOTH_PER = 60
MULT = 2.8
# ================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://bingx.com/",
}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(
            url,
            data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=15,
            headers=HEADERS
        )
    except Exception as e:
        print(f"خطا در ارسال تلگرام: {e}")

def get_top_symbols(n=300):
    try:
        r = requests.get(
            "https://open-
