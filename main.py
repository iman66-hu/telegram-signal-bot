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
    "TRXUSDT", "AVAXUSDT", "SHIBUSDT", "LINKUSDT", "SUIUSDT", "DOTUSDT", "LEOUSDT", "LTCUSDT",
    "BCHUSDT", "UNIUSDT", "PEPEUSDT", "NEARUSDT", "KASUSDT", "APTUSDT", "ICPUSDT", "XLMUSDT",
    "FETUSDT", "HBARUSDT", "ETCUSDT", "RENDERUSDT", "FILUSDT", "ATOMUSDT", "CROUSDT", "POLUSDT",
    "INJUSDT", "XMRUSDT", "TAOUSDT", "VETUSDT", "OPUSDT", "ARBUSDT", "MNTUSDT", "STXUSDT",
    "IMXUSDT", "BONKUSDT", "FLRUSDT", "WIFUSDT", "GRTUSDT", "AAVEUSDT", "THETAUSDT", "RUNEUSDT",
    "ALGOUSDT", "MKRUSDT", "SEIUSDT", "JUPUSDT", "FTMUSDT", "TIAUSDT", "LDOUSDT", "ONDOUSDT",
    "PYTHUSDT", "FLOWUSDT", "EOSUSDT", "QNTUSDT", "AXLUSDT", "SANDUSDT", "EGLDUSDT", "MANAUSDT",
    "SNXUSDT", "XTZUSDT", "DYDXUSDT", "RAYUSDT", "KCSUSDT", "ROSEUSDT", "ENSUSDT", "GALAUSDT",
    "ZECUSDT", "MINAUSDT", "NEOUSDT", "CFXUSDT", "PENDLEUSDT", "KAVAUSDT", "CHZUSDT", "COMPUSDT",
    "CRVUSDT", "1INCHUSDT", "ZROUSDT", "WLDUSDT", "APEUSDT", "BLURUSDT", "GMTUSDT", "LUNCUSDT",
    "AKTUSDT", "HOTUSDT", "ZILUSDT", "ENJUSDT", "CAKEUSDT", "MASKUSDT", "RSRUSDT", "CVXUSDT",
    "ANKRUSDT", "WAVESUSDT", "IOSTUSDT", "QTUMUSDT"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

# ================================================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15, headers=HEADERS)
    except:
        pass

def get_klines(symbol):
    url = "https://api.bybit.com/v5/market/kline"
    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": 15,
        "limit": LIMIT
    }
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            print(f"HTTP {r.status_code} for {symbol}")
            return None
        
        data = r.json()
        if data.get("retCode") != 0:
            print(f"Bybit Error {symbol}: {data.get('retMsg')}")
            return None

        kline_list = data["result"]["list"]
        if len(kline_list) < 200:
            return None

        df = pd.DataFrame(kline_list, columns=["time", "open", "high", "low", "close", "volume", "turnover"])
        df = df[["open", "high", "low", "close", "volume"]].astype(float)
        df = df.iloc[::-1].reset_index(drop=True)  # مرتب کردن از قدیم به جدید
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

# توابع استراتژی (تغییر نکرده)
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

def signal(df, symbol):
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
    print(f"🔍 Starting scan on {len(SYMBOLS)} symbols | TF: {INTERVAL}")
    sent = set()
   
    for symbol in SYMBOLS:
        try:
            df = get_klines(symbol)
            if df is None or df.empty:
                continue
               
            sig = signal(df, symbol)
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
                f"📡 Strategy: Range Filter + RMA200 (Bybit)"
            )
           
            send_telegram(msg)
            print(f"✅ {symbol} → {sig} @ {price}")
            time.sleep(0.3)
           
        except Exception as e:
            print(f"❌ {symbol} ERROR: {e}")
   
    print("🏁 Scan Finished")

if __name__ == "__main__":
    main()
