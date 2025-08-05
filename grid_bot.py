import requests
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from datetime import datetime
import time
import os

# ============ CONFIG =============

TELEGRAM_TOKEN = os.getenv("7702016556:AAEHotyy2l_TSM__loLKV9ZC7oo3duitJ8s")
CHAT_ID = os.getenv("2096206738")

INTERVAL = "1h"
LIMIT = 24
CHECK_INTERVAL = 3600  # checa a cada 1 hora
SUMMARY_INTERVAL = 10800  # envia resumo a cada 3 horas

SYMBOLS = [
    "BTC-USDT", "ETH-USDT", "SOL-USDT", "AVAX-USDT",
    "OP-USDT", "TIA-USDT", "PYTH-USDT", "INJ-USDT", "RNDR-USDT",
    "WIF-USDT", "FET-USDT", "DOGE-USDT", "NEAR-USDT", "LTC-USDT",
    "PEPE-USDT", "LINK-USDT", "SHIB-USDT", "JUP-USDT", "ARB-USDT",
    "SEI-USDT", "GRT-USDT", "MATIC-USDT", "BLUR-USDT", "DYDX-USDT"
]

# ============ FUNÇÕES =============

def get_candles(symbol: str, interval: str = "1h", limit: int = 24):
    url = f"https://api.kucoin.com/api/v1/market/candles?type={interval}&symbol={symbol}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    if data["code"] != "200000":
        return None

    df = pd.DataFrame(data["data"], columns=[
        "time", "open", "close", "high", "low", "volume", "turnover"
    ])
    df["time"] = pd.to_datetime(df["time"].astype(int), unit="s")
    df = df.iloc[::-1]  # inverter para ordem cronológica
    df[["open", "close", "high", "low", "volume"]] = df[
        ["open", "close", "high", "low", "volume"]
    ].astype(float)
    return df

def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def analyze(symbol: str):
    df = get_candles(symbol)
    if df is None or df.empty:
        return None

    rsi = RSIIndicator(close=df["close"]).rsi().iloc[-1]
    macd_line = MACD(close=df["close"]).macd().iloc[-1]
    signal_line = MACD(close=df["close"]).macd_signal().iloc[-1]

    max_price = df["high"].max()
    min_price = df["low"].min()
    current_price = df["close"].iloc[-1]
    volatility = (max_price - min_price) / current_price

    grid_high = round(current_price * 1.03, 4)
    grid_low = round(current_price * 0.97, 4)

    opportunity = (volatility >= 0.05) and (0.3 <= rsi <= 70) and (macd_line > signal_line)

    return {
        "symbol": symbol,
        "price": current_price,
        "volatility": volatility,
        "rsi": rsi,
        "macd": macd_line,
        "signal": signal_line,
        "grid_low": grid_low,
        "grid_high": grid_high,
        "opportunity": opportunity
    }

def format_message(data):
    return (
        f"🚨 *Oportunidade de Grid Detected!*\n"
        f"*Par:* `{data['symbol']}`\n"
        f"*Preço Atual:* `${data['price']:.4f}`\n"
        f"*Volatilidade 24h:* `{data['volatility']:.2%}`\n"
        f"*RSI:* `{data['rsi']:.2f}` | *MACD > Signal:* `{data['macd']:.2f} > {data['signal']:.2f}`\n"
        f"*Faixa do Grid:* `{data['grid_low']}` - `{data['grid_high']}`\n"
    )

def format_summary(results):
    summary = "*⏰ RESUMO DAS MELHORES OPORTUNIDADES (Últimas 3h)*\n\n"
    for data in results:
        summary += (
    f"📊 {pair} | RSI: {rsi:.2f} | MFI: {mfi:.2f} | Vol: {volatility:.2f}% | "
    f"Preço: {price:.2f} | Grid: {grid_min:.2f} - {grid_max:.2f} | "
    f"Grids: {grid_count} | SL: {stop_loss:.2f} | Trailing: {trailing_stop:.2f}\n")

    send_telegram_message(
    f"🔁 Grid ativo\nPar: {pair}\n"
    f"RSI: {rsi:.2f} | MFI: {mfi:.2f}\n"
    f"Preço de entrada: {price}\n"
    f"Preço limite: {price + grid_size}")









