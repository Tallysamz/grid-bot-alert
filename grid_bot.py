import os
import time
import requests
from datetime import datetime
from ta.momentum import RSIIndicator
from ta.trend import MACD
import pandas as pd

# ================= CONFIG ===================
TELEGRAM_TOKEN = os.getenv("7702016556:AAEHotyy2l_TSM__loLKV9ZC7oo3duitJ8s")
CHAT_ID = os.getenv("2096206738")
INTERVAL = 60 * 60  # verificar a cada 1 hora
RESUMO_INTERVAL = 60 * 60 * 3  # resumo a cada 3 horas

# Lista de criptos principais para análise
CRYPTOS = [
    "BTC-USDT", "ETH-USDT", "SOL-USDT", "AVAX-USDT",
    "LINK-USDT", "MATIC-USDT", "ATOM-USDT", "AR-USDT",
    "OP-USDT", "INJ-USDT", "RUNE-USDT", "TIA-USDT",
    "BLUR-USDT", "RNDR-USDT", "JUP-USDT", "PYTH-USDT",
    "SEI-USDT", "WIF-USDT", "DOGE-USDT", "SHIB-USDT"
]

# ================ FUNÇÕES ===================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Erro ao enviar mensagem:", e)

def get_ohlcv(symbol):
    url = f"https://api.kucoin.com/api/v1/market/candles?type=1hour&symbol={symbol}"
    response = requests.get(url)
    candles = response.json().get("data", [])
    if not candles:
        return None
    df = pd.DataFrame(candles, columns=["time", "open", "close", "high", "low", "volume", "turnover"])
    df = df.iloc[::-1]  # inverter
    df[["open", "close", "high", "low", "volume"]] = df[["open", "close", "high", "low", "volume"]].astype(float)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df

def analisar_cripto(symbol):
    df = get_ohlcv(symbol)
    if df is None or len(df) < 26:
        return None

    rsi = RSIIndicator(df["close"], window=14).rsi().iloc[-1]
    macd = MACD(df["close"]).macd_diff().iloc[-1]
    close = df["close"].iloc[-1]
    high = df["high"].max()
    low = df["low"].min()
    vol_24h = df["volume"].sum()
    volatilidade = ((high - low) / close) * 100

    oportunidade = rsi < 35 and macd > 0 and volatilidade > 4

    return {
        "symbol": symbol,
        "close": close,
        "rsi": round(rsi, 2),
        "macd": round(macd, 4),
        "volatilidade": round(volatilidade, 2),
        "volume": round(vol_24h, 2),
        "oportunidade": oportunidade
    }

def verificar_todas():
    oportunidades = []
    for symbol in CRYPTOS:
        try:
            dados = analisar_cripto(symbol)
            if dados and dados["oportunidade"]:
                oportunidades.append(dados)
        except Exception as e:
            print(f"Erro em {symbol}: {e}")
    return oportunidades

def formatar_mensagem(oportunidades):
    if not oportunidades:
        return "⚠️ Nenhuma oportunidade de grid encontrada no momento."
    mensagem = "🚨 <b>Oportunidades de GRID encontradas:</b>\n\n"
    for o in oportunidades:
        mensagem += (
            f"🔹 <b>{o['symbol']}</b>\n"
            f"Preço: ${o['close']}\n"
            f"RSI: {o['rsi']} | MACD: {o['macd']}\n"
            f"Volatilidade 24h: {o['volatilidade']}%\n"
            f"Volume 24h: {o['volume']}\n"
            "------------------------\n"
        )
    return mensagem

def enviar_resumo():
    resumo = []
    for symbol in CRYPTOS:
        try:
            dados = analisar_cripto(symbol)
            if dados:
                resumo.append(dados)
        except:
            continue
    mensagem = "🧾 <b>Resumo geral das criptos:</b>\n\n"
    for r in resumo:
        mensagem += (
            f"{r['symbol']} | RSI: {r['rsi']} | MACD: {r['macd']} | Vol: {r['volatilidade']}%\n"
        )
    send_telegram(mensagem)

# =============== LOOP ========================
print("🤖 Bot de Grid rodando com sucesso...")
ultimo_resumo = time.time()

while True:
    agora = time.time()
    oportunidades = verificar_todas()
    mensagem = formatar_mensagem(oportunidades)
    send_telegram(mensagem)

    if agora - ultimo_resumo >= RESUMO_INTERVAL:
        enviar_resumo()
        ultimo_resumo = agora

    time.sleep(INTERVAL)








