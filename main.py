import time
import requests
import pandas as pd
import numpy as np

# ==================== تنظیمات ====================
BOT_TOKEN = "8848229995:AAGPTk8rByw96JDp2cdU_EnE8ihWUf5v4rE"
CHAT_ID = "8430812593"
INTERVAL = "15m"
LIMIT = 300

SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", ...]  # لیستت رو بذار

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=10, headers=HEADERS)
    except:
        pass

def get_klines(symbol):
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {"symbol": symbol, "interval": INTERVAL, "limit": LIMIT}
    
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=15)
        
        if r.status_code == 451:
            print(f"🚫 Binance Blocked (451) for {symbol} - احتمالاً نیاز به VPN داری")
            return None
        if r.status_code != 200:
            print(f"HTTP {r.status_code} for {symbol}")
            return None
            
        data = r.json()
        if not isinstance(data, list) or len(data) < 200:
            return None

        df = pd.DataFrame(data, columns=["time","open","high","low","close","volume","ct","qv","n","tb","tq","i"])
        df["close"] = df["close"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        return df
        
    except Exception as e:
        print(f"Error {symbol}: {e}")
        return None
