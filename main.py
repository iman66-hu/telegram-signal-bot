import requestsimport os
import requests
import pandas as pd
import numpy as np
from ta.trend import EMAIndicator
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SYMBOLS = [
    "BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
    "DOGEUSDT","ADAUSDT","TRXUSDT","LINKUSDT","AVAXUSDT",
    "SUIUSDT","LTCUSDT","BCHUSDT","DOTUSDT","UNIUSDT",
    "AAVEUSDT","ETCUSDT","XLMUSDT","HBARUSDT","FILUSDT",
    "ATOMUSDT","NEARUSDT","APTUSDT","OPUSDT","ARBUSDT",
    "INJUSDT","SEIUSDT","TONUSDT","PEPEUSDT","SHIBUSDT",
    "ICPUSDT","MKRUSDT","RENDERUSDT","FETUSDT","WIFUSDT",
    "BONKUSDT","JUPUSDT","TIAUSDT","RUNEUSDT","GRTUSDT",
    "ALGOUSDT","VETUSDT","FLOWUSDT","EOSUSDT","EGLDUSDT",
    "SANDUSDT","MANAUSDT","THETAUSDT","XTZUSDT","KASUSDT"
]

INTERVAL = "15m"
LIMIT = 300


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text
    })


def get_klines(symbol):
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {
        "symbol": symbol,
        "interval": INTERVAL,
        "limit": LIMIT
    }

    data = requests.get(url, params=params).json()

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "ct","qv","n","tb","tq","i"
    ])

    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)

    return df
    def rma(series, length):
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
            if price.iloc[i] - rng.iloc[i] < filt[i - 1]:
                filt[i] = filt[i - 1]
            else:
                filt[i] = price.iloc[i] - rng.iloc[i]
        else:
            if price.iloc[i] + rng.iloc[i] > filt[i - 1]:
                filt[i] = filt[i - 1]
            else:
                filt[i] = price.iloc[i] + rng.iloc[i]

    return pd.Series(filt, index=price.index)


def signal(df):
    src = df["close"]

    rma200 = rma(src, 200)

    smrng = smoothrng(src, 100, 3)

    filt = rngfilt(src, smrng)

    buy = (
        filt.iloc[-2] < rma200.iloc[-2]
        and filt.iloc[-1] > rma200.iloc[-1]
    )

    sell = (
        filt.iloc[-2] > rma200.iloc[-2]
        and filt.iloc[-1] < rma200.iloc[-1]
    )

    if buy:
        return "BUY"

    if sell:
        return "SELL"

    return None
    def main():

    sent = set()

    for symbol in SYMBOLS:

        try:

            df = get_klines(symbol)

            sig = signal(df)

            if sig is None:
                continue

            key = f"{symbol}_{sig}"

            if key in sent:
                continue

            sent.add(key)

            price = round(df["close"].iloc[-1], 4)

            msg = f"""
🚨 {sig}

📌 {symbol}

⏰ TimeFrame : 15m

💰 Price : {price}

📡 Strategy :
Range Filter + RMA200
"""

            send_telegram(msg)

            time.sleep(0.3)

        except Exception as e:

            print(symbol, e)

    print("Scan Finished")


if __name__ == "__main__":
    main()
