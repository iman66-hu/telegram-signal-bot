import os
import time
import requests
import pandas as pd
import numpy as np

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

INTERVAL = "15m"
LIMIT = 300

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "TRXUSDT",
    "LINKUSDT", "AVAXUSDT", "SUIUSDT", "LTCUSDT", "BCHUSDT", "DOTUSDT", "UNIUSDT", "AAVEUSDT",
    "ETCUSDT", "XLMUSDT", "HBARUSDT", "FILUSDT", "ATOMUSDT", "NEARUSDT", "APTUSDT", "OPUSDT",
    "ARBUSDT", "INJUSDT", "SEIUSDT", "TONUSDT", "PEPEUSDT", "SHIBUSDT", "ICPUSDT", "MKRUSDT",
    "RENDERUSDT", "FETUSDT", "WIFUSDT", "BONKUSDT", "JUPUSDT", "TIAUSDT", "RUNEUSDT", "GRTUSDT",
    "ALGOUSDT", "VETUSDT", "FLOWUSDT", "EOSUSDT", "EGLDUSDT", "SANDUSDT", "MANAUSDT", "THETAUSDT",
    "XTZUSDT", "KASUSDT", "DYDXUSDT", "ZECUSDT", "COMPUSDT", "SNXUSDT", "1INCHUSDT", "CAKEUSDT",
    "KAVAUSDT", "APEUSDT", "GMTUSDT", "BLURUSDT", "ZROUSDT", "ENSUSDT", "GALAUSDT", "LDOUSDT",
    "CRVUSDT", "CFXUSDT", "CHZUSDT", "ROSEUSDT", "CELOUSDT", "MASKUSDT", "HOTUSDT", "ANKRUSDT",
    "IOSTUSDT", "ONEUSDT", "ZILUSDT", "QTUMUSDT", "ONTUSDT", "ICXUSDT", "WAVESUSDT", "RSRUSDT"
]

def send_telegram(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ Telegram credentials not set")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(
            url,
            data={"chat_id": CHAT_ID, "text": text},
            timeout=20
        )
    except Exception as e:
        print(f"Telegram send error: {e}")


def get_klines(symbol):
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {
        "symbol": symbol,
        "interval": INTERVAL,
        "limit": LIMIT
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        if r.status_code != 200:
            print(f"HTTP {r.status_code} for {symbol}")
            return None
        data = r.json()
        if not isinstance(data, list) or len(data) < 210:
            return None

        df = pd.DataFrame(data, columns=[
            "time", "open", "high", "low", "close", "volume",
            "ct", "qv", "n", "tb", "tq", "i"
        ])
        df["close"] = df["close"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None


def rma(series, length):
    """Rolling Moving Average (Wilder's)"""
    alpha = 1 / length
    out = [series.iloc[0]]
    for i in range(1, len(series)):
        out.append(alpha * series.iloc[i] + (1 - alpha) * out[-1])
    return pd.Series(out, index=series.index)


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
    if sell:
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

            sig = signal(df)
            if sig is None:
                continue

            key = f"{symbol}_{sig}"
            if key in sent:
                continue

            sent.add(key)
            price = round(float(df["close"].iloc[-1]), 4)

            msg = (
                f"🚨 {sig} SIGNAL\n\n"
                f"📌 {symbol}\n"
                f"⏰ Timeframe: {INTERVAL}\n"
                f"💰 Price: {price}\n\n"
                f"📡 Strategy: Range Filter + RMA200"
            )

            send_telegram(msg)
            print(f"✅ {symbol} → {sig} @ {price}")
            time.sleep(0.3)

        except Exception as e:
            print(f"❌ {symbol} ERROR: {e}")

    print("🏁 Scan Finished")


if __name__ == "__main__":
    main()
