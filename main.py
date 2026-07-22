import time
import requests
import pandas as pd
import numpy as np

# ==================== تنظیمات ====================
BOT_TOKEN = "8848229995:AAGPTk8rByw96JDp2cdU_EnE8ihWUf5v4rE"
CHAT_ID = "8430812593"
INTERVAL = "15m"
LIMIT = 300

# ==================== ۱۰۰ ارز برتر ====================
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "TONUSDT", "ADAUSDT",
    "TRXUSDT", "AVAXUSDT", "SHIBUSDT", "LINKUSDT", "SUIUSDT", "DOTUSDT", "LTCUSDT", "BCHUSDT",
    "UNIUSDT", "PEPEUSDT", "NEARUSDT", "APTUSDT", "ICPUSDT", "XLMUSDT", "FETUSDT", "HBARUSDT",
    "ETCUSDT", "RENDERUSDT", "FILUSDT", "ATOMUSDT", "INJUSDT", "XMRUSDT", "VETUSDT", "OPUSDT",
    "ARBUSDT", "STXUSDT", "IMXUSDT", "BONKUSDT", "WIFUSDT", "GRTUSDT", "AAVEUSDT", "THETAUSDT",
    "RUNEUSDT", "ALGOUSDT", "MKRUSDT", "SEIUSDT", "JUPUSDT", "FTMUSDT", "TIAUSDT", "LDOUSDT",
    "ONDOUSDT", "PYTHUSDT", "FLOWUSDT", "EOSUSDT", "QNTUSDT", "SANDUSDT", "EGLDUSDT", "MANAUSDT",
    "SNXUSDT", "XTZUSDT", "DYDXUSDT", "ROSEUSDT", "ENSUSDT", "GALAUSDT", "ZECUSDT", "NEOUSDT",
    "CFXUSDT", "PENDLEUSDT", "KAVAUSDT", "CHZUSDT", "COMPUSDT", "CRVUSDT", "1INCHUSDT", "ZROUSDT",
    "WLDUSDT", "APEUSDT", "BLURUSDT", "GMTUSDT", "HOTUSDT", "ZILUSDT", "ENJUSDT", "CAKEUSDT",
    "MASKUSDT", "RSRUSDT", "ANKRUSDT", "WAVESUSDT", "IOSTUSDT", "QTUMUSDT", "KASUSDT", "TAOUSDT",
    "MNTUSDT", "POLUSDT", "CROUSDT", "FLRUSDT", "RAYUSDT", "KCSUSDT", "MINAUSDT", "AKTUSDT",
    "CVXUSDT", "LUNCUSDT"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.weex.com/",
}

# ================================================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15, headers=HEADERS)
    except:
        pass

def get_klines(symbol):
    url = "https://api-contract.weex.com/capi/v2/market/candles"
    params = {
        "symbol": f"cmt_{symbol.lower()}",
        "granularity": "15m",
        "limit": LIMIT
    }
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=20)
        print(f"{symbol} → Status: {r.status_code}")
        
        if r.status_code != 200:
            return None
        
        data = r.json()
        if not isinstance(data, list) or len(data) < 200:
            return None

        df = pd.DataFrame(data, columns=["time", "open", "high", "low", "close", "volume", "turnover"])
        df = df[["open", "high", "low", "close", "volume"]].astype(float)
        df = df.iloc[::-1].reset_index(drop=True)   # مرتب کردن از قدیمی به جدید
        return df
    except Exception as e:
        print(f"Error {symbol}: {e}")
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
    print(f"🔍 Starting scan on {len(SYMBOLS)} symbols | TF: {INTERVAL} | WEEX")
    sent = set()
   
    for symbol in SYMBOLS:
        try:
            df = get_klines(symbol)
            if df is None or df.empty:
                continue
               
            sig = signal(df)
            if sig is None:
                continue
               
            key = f"{symbol}_{sig}"
            if key in sent:
                continue
               
            sent.add(key)
            price = round(float(df["close"].iloc[-1]), 4)
           
            msg = (
                f"🚨 <b>{sig} SIGNAL</b>\n\n"
                f"📌 <b>{symbol}</b>\n"
                f"⏰ Timeframe: {INTERVAL}\n"
                f"💰 Price: <b>{price}</b>\n\n"
                f"📡 Exchange: WEEX | Strategy: Range Filter + RMA200"
            )
           
            send_telegram(msg)
            print(f"✅ {symbol} → {sig} @ {price}")
            time.sleep(0.4)
           
        except Exception as e:
            print(f"❌ {symbol} ERROR: {e}")
   
    print("🏁 Scan Finished")

if __name__ == "__main__":
    main()
