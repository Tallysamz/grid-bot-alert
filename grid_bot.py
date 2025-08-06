import os
import time
import requests
import pandas as pd
from datetime import datetime
from ta.momentum import RSIIndicator
from ta.trend import MACD
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  
CHAT_ID = os.getenv("CHAT_ID")

SYMBOLS = [
    "BTC-USDT", "ETH-USDT", "SOL-USDT", "AVAX-USDT", "ADA-USDT", "MATIC-USDT",
    "XRP-USDT", "DOT-USDT", "TRX-USDT", "LTC-USDT", "LINK-USDT", "BCH-USDT",
    "UNI-USDT", "XLM-USDT", "ATOM-USDT", "NEAR-USDT", "ETC-USDT", "APT-USDT",
    "FIL-USDT", "EGLD-USDT", "SAND-USDT", "AAVE-USDT", "FTM-USDT", "GRT-USDT", "RUNE-USDT"
]

INTERVAL = "1h"
LIMIT = 50

STOP_LOSS_PCT = 5
TRAILING_STOP_PCT = 3

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Erro ao enviar mensagem:", e)

def get_klines(symbol):
    url = f"https://api.kucoin.com/api/v1/market/candles?type={INTERVAL}&symbol={symbol}&limit={LIMIT}"
    response = requests.get(url)
    data = response.json()
    if "data" not in data or not data["data"]:
        return None
    df = pd.DataFrame(data["data"], columns=["time", "open", "close", "high", "low", "volume", "turnover"])
    df = df.iloc[::-1]
    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["time"] = pd.to_datetime(df["time"].astype(int), unit="s")
    return df

def analyze_symbol(symbol):
    df = get_klines(symbol)
    if df is None or df.empty:
        return None

    price_now = df["close"].iloc[-1]
    max_price = df["high"].max()
    min_price = df["low"].min()
    volatility = (max_price - min_price) / price_now * 100

    rsi = RSIIndicator(close=df["close"], window=14).rsi().iloc[-1]
    macd_calc = MACD(close=df["close"])
    macd_val = macd_calc.macd().iloc[-1]
    signal_val = macd_calc.macd_signal().iloc[-1]

    if 30 <= rsi <= 70 and macd_val > signal_val:
        grid_min = price_now * (1 - volatility / 100 / 2)
        grid_max = price_now * (1 + volatility / 100 / 2)

        message = (
            f"🚨 *Oportunidade Detectada!*\n"
            f"*Cripto:* {symbol}\n"
            f"*Preço Atual:* {price_now:.2f} USDT\n"
            f"*Volatilidade:* {volatility:.2f}%\n"
            f"*RSI:* {rsi:.2f}\n"
            f"*MACD > Sinal:* ✅\n"
            f"*Faixa de Grid:* {grid_min:.2f} - {grid_max:.2f}\n"
            f"*Stop Loss:* {price_now * (1 - STOP_LOSS_PCT / 100):.2f} (-{STOP_LOSS_PCT}%)\n"
            f"*Trailing Stop:* {TRAILING_STOP_PCT}%"
        )
        return message
    return None

def resumo_geral():
    resumo = "*📊 Resumo Geral - Análise de Mercado*\n\n"
    for symbol in SYMBOLS:
        df = get_klines(symbol)
        if df is None or df.empty:
            continue
        price_now = df["close"].iloc[-1]
        max_price = df["high"].max()
        min_price = df["low"].min()
        volatility = (max_price - min_price) / price_now * 100
        rsi = RSIIndicator(close=df["close"], window=14).rsi().iloc[-1]
        macd_calc = MACD(close=df["close"])
        macd_val = macd_calc.macd().iloc[-1]
        signal_val = macd_calc.macd_signal().iloc[-1]
        resumo += (
            f"*{symbol}*\n"
            f"• Preço: {price_now:.2f} USDT\n"
            f"• Volatilidade: {volatility:.2f}%\n"
            f"• RSI: {rsi:.2f}\n"
            f"• MACD > Sinal: {'✅' if macd_val > signal_val else '❌'}\n\n"
        )
    send_telegram_message(resumo)

def main():
    contador_resumo = 0
    while True:
        for symbol in SYMBOLS:
            msg = analyze_symbol(symbol)
            if msg:
                send_telegram_message(msg)
            time.sleep(1)

        contador_resumo += 1
        if contador_resumo >= 3:  # a cada 3 horas
            resumo_geral()
            contador_resumo = 0

        time.sleep(3600)

if __name__ == "__main__":
    main()













