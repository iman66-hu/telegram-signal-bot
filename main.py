import time
import requests
import pandas as pd
import numpy as np

BOT_TOKEN = "8848229995:AAGPTk8rByw96JDp2cdU_EnE8ihWUf5v4rE"
CHAT_ID = "8430812593"
INTERVAL = "15m"
LIMIT = 300

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.binance.com/",
    "Origin": "https://www.binance.com",
}

def get_klines(symbol):
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {"symbol": symbol, "interval": INTERVAL, "limit": LIMIT}
    
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=20)
        print(f"{symbol} → Status: {r.status_code}")   # برای دیباگ
        
        if r.status_code == 200:
            data = r.json()
            df = pd.DataFrame(data, columns=["time","open","high","low","close","volume","ct","qv","n","tb","tq","i"])
            df = df[["close", "high", "low"]].astype(float)
            return df
        else:
            return None
    except Exception as e:
        print(f"Error {symbol}: {e}")
        return None

# تابع‌های rma, smoothrng, rngfilt, signal رو مثل قبل نگه دار
# ... (کد قبلی رو کپی کن)

if __name__ == "__main__":
    main()
