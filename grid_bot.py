import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime
import telegram
import asyncio

# === CONFIGURAÇÕES ===
TOKEN = "7702016556:AAEHotyy2l_TSM__loLKV9ZC7oo3duitJ8s"
CHAT_ID = "2096206738"
symbols = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT",
    "XRPUSDT", "MATICUSDT", "ADAUSDT", "DOGEUSDT",
    "TRXUSDT", "DOTUSDT", "LINKUSDT", "ATOMUSDT"
]

# Parâmetros do grid
trailing_stop_pct = 0.03
stop_loss_pct = 0.05
grid_count = 10
min_volatility = 2.5

# === FUNÇÕES ===

def get_klines(symbol, interval="15m", limit=96):
    url = f"https://api.kucoin.com/api/v1/market/candles?type={interval}&symbol={symbol}&limit={limit}"
    response = requests.get(url)
    data = response.json()["data"]
    df = pd.DataFrame(data, columns=["time", "open", "close", "high", "low", "vol", "turnover"])
    df["time"] = pd.to_datetime(df["time"].astype(int), unit="s")
    df = df.iloc[::-1].reset_index(drop=True)
    df[["open", "close", "high", "low"]] = df[["open", "close", "high", "low"]].astype(float)
    return df

def calc_rsi(prices, period=14):
    delta = prices.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calc_macd(prices, fast=12, slow=26, signal=9):
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line

def analyze_symbol(symbol):
    try:
        df = get_klines(symbol)
        if df is None or df.empty:
            return None

        df["return"] = df["close"].pct_change()
        volatility = df["return"].std() * 100

        rsi = calc_rsi(df["close"]).iloc[-1]
        macd_line, signal_line = calc_macd(df["close"])
        macd_cross = macd_line.iloc[-1] > signal_line.iloc[-1]

        price = df["close"].iloc[-1]
        lower_price = price * (1 - (volatility / 100) / 2)
        upper_price = price * (1 + (volatility / 100) / 2)
        grid_spacing = (upper_price - lower_price) / grid_count

        stop_loss = price * (1 - stop_loss_pct)
        trailing_stop = price * (1 + trailing_stop_pct)

        if volatility >= min_volatility and 40 < rsi < 70 and macd_cross:
            return {
                "symbol": symbol,
                "price": price,
                "volatility": round(volatility, 2),
                "lower": round(lower_price, 4),
                "upper": round(upper_price, 4),
                "grids": grid_count,
                "spacing": round(grid_spacing, 4),
                "stop_loss": round(stop_loss, 4),
                "trailing_stop": round(trailing_stop, 4),
                "rsi": round(rsi, 2),
                "macd_cross": macd_cross
            }
    except Exception as e:
        print(f"[ERRO] {symbol}: {e}")
    return None

async def send_message(bot, chat_id, message):
    await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")

async def main():
    bot = telegram.Bot(token=TOKEN)
    results = []

    for symbol in symbols:
        result = analyze_symbol(symbol)
        if result:
            results.append(result)

    if results:
        text = "<b>📊 Oportunidades de Grid Spot (KuCoin)</b>\n\n"
        for r in results:
            text += (
                f"<b>{r['symbol']}</b> 🟢\n"
                f"💰 Preço: <b>{r['price']}</b>\n"
                f"📈 Volatilidade: <b>{r['volatility']}%</b>\n"
                f"📊 RSI: <b>{r['rsi']}</b>\n"
                f"📉 Faixa: <b>{r['lower']} - {r['upper']}</b>\n"
                f"📌 Grids: <b>{r['grids']}</b> (Espaço: {r['spacing']})\n"
                f"🛑 SL: <b>{r['stop_loss']}</b> | 🔁 TS: <b>{r['trailing_stop']}</b>\n\n"
            )
        await send_message(bot, CHAT_ID, text)
    else:
        print("Nenhuma oportunidade encontrada.")

# === EXECUÇÃO ===
if __name__ == "__main__":
    asyncio.run(main())








