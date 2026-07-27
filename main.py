import time
import requests
import pandas as pd
import numpy as np

# ==================== تنظیمات ====================
BOT_TOKEN = "YOUR_NEW_BOT_TOKEN"          # توکن جدید بگذار
CHAT_ID   = "YOUR_CHAT_ID"
INTERVALS = ["15m"]                       # فقط ۱۵ دقیقه
LIMIT     = 300

# پارامترهای استراتژی (مطابق Pine)
RMA_LEN   = 200
PER       = 100                           # دوره نمونه‌برداری
MULT      = 3.0                           # ضریب محدوده
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
    except Exception:
        pass

def get_top_symbols(n=300):
    try:
        r = requests.get(
            "https://open-api.bingx.com/openApi/swap/v2/quote/ticker",
            headers=HEADERS,
            timeout=20
        )
        data = r.json().get("data", [])
        usdt_pairs = [
            item for item in data
            if item["symbol"].endswith("-USDT")
            and not item["symbol"].startswith("NC")
            and float(item.get("quoteVolume", 0)) > 0
        ]
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
        if not isinstance(data, list) or len(data) < 210:
            return None
        df = pd.DataFrame(data)
        df = df[["open", "high", "low", "close", "volume"]].astype(float)
        df = df.iloc[::-1].reset_index(drop=True)  # قدیمی → جدید
        return df
    except Exception as e:
        print(f"Error {symbol} {interval}: {e}")
        return None

# ==================== توابع دقیقاً مطابق Pine Script ====================

def rma(series, length):
    """ta.rma → Wilder's smoothing (alpha = 1/length)"""
    return series.ewm(alpha=1 / length, adjust=False).mean()

def smoothrng(x, t=100, m=3.0):
    """
    مطابق Pine:
    wper = t * 2 - 1
    avrng = ta.ema(abs(x - x[1]), t)
    smoothrng = ta.ema(avrng, wper) * m
    """
    wper = t * 2 - 1
    avrng = (x - x.shift(1)).abs().ewm(span=t, adjust=False).mean()
    return avrng.ewm(span=wper, adjust=False).mean() * m

def rngfilt(price, rng):
    """
    مطابق Pine:
    filt := x > nz(filt[1]) ?
         max(x - r, nz(filt[1])) :
         min(x + r, nz(filt[1]))
    """
    filt = np.zeros(len(price))
    filt[0] = price.iloc[0]
    for i in range(1, len(price)):
        prev = filt[i - 1]
        if price.iloc[i] > prev:
            filt[i] = max(prev, price.iloc[i] - rng.iloc[i])
        else:
            filt[i] = min(prev, price.iloc[i] + rng.iloc[i])
    return pd.Series(filt, index=price.index)

def signal(df):
    if df is None or len(df) < 210:
        return None, None

    src = df["close"]
    rma200 = rma(src, RMA_LEN)
    smrng  = smoothrng(src, PER, MULT)
    filt   = rngfilt(src, smrng)

    # جلوگیری از ری‌پینت (فقط کندل‌های بسته‌شده)
    # iloc[-1] = کندل جاری (باز)
    # iloc[-2] = آخرین کندل بسته‌شده
    # iloc[-3] = کندل قبل از آن
    if (pd.isna(filt.iloc[-2]) or pd.isna(rma200.iloc[-2]) or
        pd.isna(filt.iloc[-3]) or pd.isna(rma200.iloc[-3])):
        return None, None

    # کراس صعودی → BUY  (ta.crossover(filt, rma))
    buy = (filt.iloc[-3] < rma200.iloc[-3]) and (filt.iloc[-2] > rma200.iloc[-2])

    # کراس نزولی → SELL (ta.crossunder(filt, rma))
    sell = (filt.iloc[-3] > rma200.iloc[-3]) and (filt.iloc[-2] < rma200.iloc[-2])

    if buy:
        return "BUY", float(df["close"].iloc[-2])
    if sell:
        return "SELL", float(df["close"].iloc[-2])
    return None, None

def main():
    symbols = get_top_symbols(300)
    if not symbols:
        print("❌ هیچ نمادی پیدا نشد")
        return

    print(f"🔍 شروع اسکن روی {len(symbols)} نماد | تایم‌فریم: ۱۵ دقیقه | صرافی: BingX")
    print(f"📊 استراتژی: Range Filter (per={PER}, mult={MULT}) + RMA {RMA_LEN}")

    sent = set()
    for symbol in symbols:
        for interval in INTERVALS:
            try:
                df = get_klines(symbol, interval)
                if df is None or df.empty:
                    continue

                sig, price = signal(df)
                if sig is None:
                    continue

                key = f"{symbol}_{interval}_{sig}"
                if key in sent:
                    continue
                sent.add(key)

                price = round(price, 6 if price < 1 else 4)
                emoji = "🟢" if sig == "BUY" else "🔴"
                msg = (
                    f"{emoji} <b>سیگنال {sig}</b>\n\n"
                    f"📌 <b>{symbol}</b>\n"
                    f"⏰ تایم‌فریم: <b>{interval}</b>\n"
                    f"💰 قیمت: <b>{price}</b>\n\n"
                    f"📡 صرافی: BingX\n"
                    f"📊 استراتژی: Range Filter + RMA {RMA_LEN}"
                )
                send_telegram(msg)
                print(f"✅ {symbol} | {interval} → {sig} @ {price}")
                time.sleep(0.3)
            except Exception as e:
                print(f"❌ {symbol} {interval} ERROR: {e}")

    print("🏁 اسکن تمام شد")

if __name__ == "__main__":
    main()
