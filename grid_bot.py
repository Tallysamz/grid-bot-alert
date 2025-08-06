import os
import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.trend import MACD
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
STOP_LOSS_PCT = 3
TRAILING_STOP_PCT = 3

def get_klines(symbol, interval='1hour', limit=24):
    url = f"https://api.kucoin.com/api/v1/market/candles?type={interval}&symbol={symbol}&limit={limit}"
    try:
        response = requests.get(url)
        data_json = response.json()

        data = data_json.get("data", [])
        if not data:
            print(f"Erro: dados vazios para {symbol}")
            return None

        df = pd.DataFrame(data, columns=["time", "open", "close", "high", "low", "volume", "turnover"])
        df = df.iloc[::-1]  # Ordem cronológica
        df[["open", "close", "high", "low", "volume"]] = df[["open", "close", "high", "low", "volume"]].astype(float)
        return df
    except Exception as e:
        print(f"Erro ao buscar dados de {symbol}: {e}")
        return None

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

    volume_avg = df["volume"].tail(20).mean()
    volume_now = df["volume"].iloc[-1]

    # Filtros de segurança
    rsi_ok = 40 <= rsi <= 60
    macd_ok = macd_val > signal_val
    volume_ok = volume_now > volume_avg * 1.1
    volatilidade_ok = volatility > 2

    if rsi_ok and macd_ok and volume_ok and volatilidade_ok:
        grid_min = price_now * (1 - volatility / 100 / 2)
        grid_max = price_now * (1 + volatility / 100 / 2)
        stop_loss = price_now * (1 - STOP_LOSS_PCT / 100)

        message = (
            f"🚨 *Oportunidade Detectada!*\n"
            f"🪙 *Cripto:* {symbol}\n"
            f"💰 *Preço Atual:* {price_now:.2f} USDT\n"
            f"📊 *Volatilidade 24h:* {volatility:.2f}%\n"
            f"📈 *RSI (14):* {rsi:.2f}\n"
            f"📉 *MACD > Sinal:* ✅\n"
            f"📦 *Volume Atual:* {volume_now:.2f} (média: {volume_avg:.2f})\n"
            f"🔁 *Faixa de Grid:* {grid_min:.2f} - {grid_max:.2f}\n"
            f"🛡️ *Stop Loss:* {stop_loss:.2f} (-{STOP_LOSS_PCT}%)\n"
            f"🎯 *Trailing Stop:* {TRAILING_STOP_PCT}%"
        )
        return message
    return None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    response = requests.post(url, data=data)
    if response.status_code != 200:
        print(f"Erro ao enviar mensagem: {response.text}")

# Lista de moedas para monitorar (sem MATIC, RNDR, GALA)
symbols = [
    "BTC-USDT", "ETH-USDT", "AVAX-USDT", "SOL-USDT", "ADA-USDT", "XRP-USDT",
    "AR-USDT", "LTC-USDT", "FET-USDT", "OP-USDT", "INJ-USDT", "TIA-USDT",
    "NEAR-USDT", "DOGE-USDT", "PEPE-USDT", "BLUR-USDT", "SUI-USDT", "PYTH-USDT",
    "ORDI-USDT", "TRB-USDT", "ZRX-USDT", "MINA-USDT"
]

# Executar análise
for symbol in symbols:
    msg = analyze_symbol(symbol)
    if msg:
        send_telegram_message(msg)

















