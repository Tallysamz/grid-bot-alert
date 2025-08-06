import requests
import pandas as pd
import numpy as np
import os
import time
from datetime import datetime
from ta.momentum import RSIIndicator, MoneyFlowIndex
from ta.trend import MACD
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SYMBOLS = [
    "BTC-USDT", "ETH-USDT", "SOL-USDT", "ADA-USDT", "XRP-USDT",
    "DOGE-USDT", "AVAX-USDT", "DOT-USDT", "MATIC-USDT", "BNB-USDT",
    "LINK-USDT", "ATOM-USDT", "LTC-USDT", "BCH-USDT", "FIL-USDT",
    "AAVE-USDT", "NEAR-USDT", "SAND-USDT", "AXS-USDT", "APE-USDT",
    "RNDR-USDT", "FTM-USDT", "VET-USDT", "ICP-USDT", "HBAR-USDT"
]

INTERVAL = "1h"
LIMIT = 50
TRAILING_STOP_PCT = 0.03  # 3%
STOP_LOSS_PCT = 0.05      # 5%


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=payload)


def get_klines(symbol):
    url = f"https://api.kucoin.com/api/v1/market/candles?type={INTERVAL}&symbol={symbol}&limit={LIMIT}"
    response = requests.get(url)
    data = response.json()['data']
    df = pd.DataFrame(data, columns=["time", "open", "close", "high", "low", "volume", "turnover"])
    df = df.iloc[::-1].reset_index(drop=True)
    df[["open", "close", "high", "low", "volume"]] = df[["open", "close", "high", "low", "volume"]].astype(float)
    return df


def analyze_symbol(symbol):
    try:
        df = get_klines(symbol)
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']

        rsi = RSIIndicator(close).rsi().iloc[-1]
        mfi = MoneyFlowIndex(high, low, close, volume).money_flow_index().iloc[-1]
        macd = MACD(close)
        macd_line = macd.macd().iloc[-1]
        macd_signal = macd.macd_signal().iloc[-1]

        if not (30 < rsi < 70):
            return
        if mfi >= 80:
            return
        if macd_line <= macd_signal:
            return

        current_price = close.iloc[-1]
        volatility = np.std(close) / np.mean(close)

        grid_range_pct = 0.06  # 6% de faixa
        lower_bound = current_price * (1 - grid_range_pct / 2)
        upper_bound = current_price * (1 + grid_range_pct / 2)
        stop_loss = lower_bound * (1 - STOP_LOSS_PCT)
        trailing_stop = current_price * (1 - TRAILING_STOP_PCT)

        message = (
            f"<b>Oportunidade Detectada! 🚨</b>\n"
            f"Cripto: <b>{symbol}</b>\n"
            f"Preço Atual: <code>{current_price:.2f}</code>\n"
            f"RSI: <code>{rsi:.2f}</code> | MFI: <code>{mfi:.2f}</code>\n"
            f"MACD: <code>{macd_line:.4f}</code> > Sinal: <code>{macd_signal:.4f}</code>\n"
            f"Volatilidade: <code>{volatility*100:.2f}%</code>\n"
            f"Faixa de Grid: <code>{lower_bound:.2f} - {upper_bound:.2f}</code>\n"
            f"Stop Loss: <code>{stop_loss:.2f}</code>\n"
            f"Trailing Stop: <code>{trailing_stop:.2f}</code>"
        )
        send_telegram_message(message)

    except Exception as e:
        print(f"Erro ao analisar {symbol}: {e}")


if __name__ == "__main__":
    while True:
        print("Iniciando análise das criptomoedas...")
        for symbol in SYMBOLS:
            analyze_symbol(symbol)
            time.sleep(1.5)  # Para evitar rate limit
        print("Análise concluída. Aguardando 1 hora...")
        time.sleep(3600)  # Executa a cada 1h












