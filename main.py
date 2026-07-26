import time
import requests
import pandas as pd
import numpy as np

# ==================== تنظیمات ====================
BOT_TOKEN = "8848229995:AAGPTk8rByw96JDp2cdU_EnE8ihWUf5v4rE"
CHAT_ID = "8430812593"
INTERVALS = ["5m", "15m", "30m"]   # تایم‌فریم‌های مورد نظر
LIMIT = 300
# ================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://bingx.com/",
}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15, headers=HEADERS)
    except:
        pass

def get_top_symbols(n=300):
    """گرفتن ۳۰۰ ارز برتر بر اساس حجم معامله ۲۴ ساعته از BingX"""
    try:
        r = requests.get("https://open-api.bingx.com/openApi/swap/v2/quote/ticker", headers=HEADERS, timeout=20)
        data = r.json().get("data", [])
        
        # فقط جفت‌های USDT کریپتو (حذف سهام و ایندکس‌ها)
        usdt_pairs = [
            item for item in data
            if item["symbol"].endswith("-USDT")
            and not item["symbol"].startswith("NC")
            and float(item.get("quoteVolume", 0)) > 0
        ]
        
        # مرتب‌سازی بر اساس حجم (نزولی)
        usdt_pairs.sort(key=lambda x: float(x["quoteVolume"]), reverse=True)
        
        symbols = [item["symbol"] for item in usdt_pairs[:n]]
        print(f"✅ {len(symbols)} نماد برتر از BingX بارگذاری شد")
        return symbols
    except Exception as e:
        print(f"❌ خطا در گرفتن لیست نمادها: {e}")
        return []

def get_klines(symbol, interval):
    url = "https://open-api.bingx.com/openApi/swap/v3/quote/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": LIMIT
    }
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            return None
        
        data = r.json().get("data", [])
        if not isinstance(data, list) or len(data) < 200:
            return None
        
        df = pd.DataFrame(data)
        df = df[["open", "high", "low", "close", "volume"]].astype(float)
        df = df.iloc[::-1].reset_index(drop=True)  # از قدیمی به جدید
        return df
    except Exception as e:
        print(f"Error {symbol} {interval}: {e}")
        return None

# توابع استراتژی
def rma(series, length):
    return series.ewm(alpha=1/length, adjust=False).mean()

def smoothrng(x, t=100, m=3.0):
    avrng = (x - x.shift(1)).abs().ewm(span=t, adjust=False).mean()
    wper = t * 2 - 1
    return avrng.ewm(span=wper, adjust=False).mean() * m

def rngfilt(price, rng):
    filt = np.zeros(len(price))
    filt[0] = price.iloc[0]
    for i in range(1, len(price)):
        if price.iloc[i] > filt[i - 1]:
            filt[i] = max(filt[i - 1], price.iloc[i] - rng.iloc[i])
        else:
            filt[i] = min(filt[i - 1], price.iloc[i] + rng.iloc[i])
    return pd.Series(filt, index=price.index)

def signal(df):
    if df is None or len(df) < 210:
        return None
  
    src = df["close"]
    rma200 = rma(src, 200)
    smrng = smoothrng(src, 100, 3.0)
    filt = rngfilt(src, smrng)
   
    if pd.isna(filt.iloc[-1]) or pd.isna(rma200.iloc[-1]):
        return None
    buy = (filt.iloc[-2] < rma200.iloc[-2]) and (filt.iloc[-1] > rma200.iloc[-1])
    sell = (filt.iloc[-2] > rma200.iloc[-2]) and (filt.iloc[-1] < rma200.iloc[-1])
    if buy:
        return "BUY"
    elif sell:
        return "SELL"
    return None

def main():
    symbols = get_top_symbols(300)
    if not symbols:
        print("❌ هیچ نمادی پیدا نشد")
        return

    print(f"🔍 Starting scan on {len(symbols)} symbols | TFs: {INTERVALS} | BingX")
    sent = set()
  
    for symbol in symbols:
        for interval in INTERVALS:
            try:
                df = get_klines(symbol, interval)
                if df is None or df.empty:
                    continue
                  
                sig = signal(df)
                if sig is None:
                    continue
                  
                key = f"{symbol}_{interval}_{sig}"
                if key in sent:
                    continue
                  
                sent.add(key)
                price = round(float(df["close"].iloc[-1]), 6)
              
                msg = (
                    f"🚨 <b>{sig} SIGNAL</b>\n\n"
                    f"📌 <b>{symbol}</b>\n"
                    f"⏰ Timeframe: {interval}\n"
                    f"💰 Price: <b>{price}</b>\n\n"
                    f"📡 Exchange: BingX | Strategy: Range Filter + RMA200"
                )
              
                send_telegram(msg)
                print(f"✅ {symbol} | {interval} → {sig} @ {price}")
                time.sleep(0.3)
              
            except Exception as e:
                print(f"❌ {symbol} {interval} ERROR: {e}")
  
    print("🏁 Scan Finished")

if __name__ == "__main__":
    main()
