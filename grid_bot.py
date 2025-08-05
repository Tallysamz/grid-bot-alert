import requests
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from datetime import datetime, timezone, timedelta
import csv
import os
import time

# ============ CONFIG =============
TELEGRAM_TOKEN = os.getenv( "7702016556:AAEHotyy2l_TSM__loLKV9ZC7oo3duitJ8s")
CHAT_ID = os.getenv( "2096206738")

SYMBOLS = [
    "BTC-USDT", "ETH-USDT", "SOL-USDT", "ADA-USDT", "XRP-USDT",
    "DOGE-USDT", "AVAX-USDT", "DOT-USDT", "MATIC-USDT", "BNB-USDT",
    "LINK-USDT", "ATOM-USDT", "LTC-USDT", "BCH-USDT", "FIL-USDT",
    "AAVE-USDT", "NEAR-USDT", "SAND-USDT", "AXS-USDT", "APE-USDT",
    "RNDR-USDT", "FTM-USDT", "VET-USDT", "ICP-USDT", "HBAR-USDT"
]

NUM_GRIDS = 10
STOP_LOSS_PERCENT = 0.03  # 3%
TAKE_PROFIT_PERCENT = 0.03
MIN_VOLATILIDADE = 2.5    # filtro mínimo de volatilidade (%)
MAX_VOLATILIDADE = 8.0    # filtro máximo de volatilidade (%)
MAX_RSI_ALERTA = 40       # RSI deve estar abaixo disso para alerta
MIN_VOLUME = 1_000_000    # volume mínimo 24h para alerta
LOG_FILE = "log.csv"

# ============ FUNÇÕES =============

def get_market_data(symbol):
    url = f"https://api.kucoin.com/api/v1/market/stats?symbol={symbol}"
    response = requests.get(url)
    data = response.json()
    if data["code"] == "200000":
        return {
            "price": float(data["data"]["last"]),
            "high": float(data["data"]["high"]),
            "low": float(data["data"]["low"]),
            "vol": float(data["data"]["volValue"])  # volume em valor (USDT)
        }
    else:
        raise Exception(f"Erro ao buscar dados de mercado para {symbol}")

def get_candles(symbol):
    url = f"https://api.kucoin.com/api/v1/market/candles?type=1hour&symbol={symbol}"
    response = requests.get(url)
    data = response.json()
    if data["code"] == "200000":
        candles = data["data"]
        df = pd.DataFrame(candles, columns=["time", "open", "close", "high", "low", "volume", "turnover"])
        df = df.astype(float)
        df = df.iloc[::-1].reset_index(drop=True)  # ordem cronológica
        return df
    else:
        raise Exception(f"Erro ao buscar candles para {symbol}")

def calcular_indicadores(df):
    rsi = RSIIndicator(close=df["close"], window=14).rsi().iloc[-1]
    macd = MACD(close=df["close"])
    macd_line = macd.macd().iloc[-1]
    signal_line = macd.macd_signal().iloc[-1]
    return round(rsi, 2), round(macd_line, 2), round(signal_line, 2)

def calcular_faixa_grid(preco, high, low):
    volatilidade = (high - low) / preco
    faixa_percent = min(max(volatilidade, 0.01), 0.10)  # mínimo 1%, máximo 10%
    preco_min = preco * (1 - faixa_percent)
    preco_max = preco * (1 + faixa_percent)
    return preco_min, preco_max, volatilidade * 100

def calcular_precos_grids(preco_min, preco_max, num_grids):
    step = (preco_max - preco_min) / num_grids
    return [round(preco_min + i * step, 2) for i in range(num_grids + 1)]

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    print("Resposta do Telegram:", response.text)

def salvar_log(data):
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow([
                "DataHoraUTC", "Par", "Preço", "High", "Low", "Volatilidade",
                "Volume", "RSI", "MACD_Line", "Signal_Line", "Status"
            ])
        writer.writerow(data)

def gerar_resumo(oportunidades):
    if not oportunidades:
        return "Nenhuma oportunidade identificada nas últimas 3 horas."

    resumo = "🕒 RESUMO DAS ÚLTIMAS 3 HORAS:\n\n"
    for opp in oportunidades:
        resumo += (
            f"📈 {opp['symbol']} | Vol: {opp['volatilidade']:.2f}%\n"
            f"💰 Faixa: {opp['preco_min']:.4f} - {opp['preco_max']:.4f}\n"
            f"🔢 Grids: {NUM_GRIDS}\n\n"
        )
    return resumo

# ============ EXECUÇÃO PRINCIPAL =============

def main():
    oportunidades = []

    for symbol in SYMBOLS:
        try:
            market_data = get_market_data(symbol)
            preco_atual = market_data["price"]
            high = market_data["high"]
            low = market_data["low"]
            vol = market_data["vol"]

            candles_df = get_candles(symbol)
            if candles_df.isnull().values.any():
                raise Exception(f"Candles incompletos para {symbol}")

            rsi, macd_line, signal_line = calcular_indicadores(candles_df)

            preco_min, preco_max, volatilidade = calcular_faixa_grid(preco_atual, high, low)
            grids = calcular_precos_grids(preco_min, preco_max, NUM_GRIDS)
            stop_loss = preco_atual * (1 - STOP_LOSS_PERCENT)
            take_profit = preco_atual * (1 + TAKE_PROFIT_PERCENT)

            status = "SEM ALERTA"

            # FILTROS PRECISOS PARA ALERTA
            if (
                MIN_VOLATILIDADE <= volatilidade <= MAX_VOLATILIDADE
                and vol >= MIN_VOLUME
                and rsi < MAX_RSI_ALERTA
            ):
                mensagem = (
                    f"*📊 Grid Bot PRO - SINAL GERADO!*\n"
                    f"🔹 *Par:* {symbol}\n"
                    f"💰 *Preço Atual:* ${preco_atual:.2f}\n"
                    f"📈 *Alta 24h:* ${high:.2f}\n"
                    f"📉 *Baixa 24h:* ${low:.2f}\n"
                    f"🌊 *Volatilidade:* {volatilidade:.2f}%\n"
                    f"📦 *Volume 24h:* {vol:.2f}\n"
                    f"📊 *RSI(14):* {rsi}\n"
                    f"📊 *MACD Line:* {macd_line}\n"
                    f"📊 *Signal Line:* {signal_line}\n"
                    f"📏 *Faixa do Grid:* ${preco_min:.2f} - ${preco_max:.2f}\n"
                    f"🔢 *Número de Grids:* {NUM_GRIDS}\n"
                    f"🚫 *Stop Loss:* ${stop_loss:.2f}\n"
                    f"🎯 *Take Profit:* ${take_profit:.2f}\n"
                    f"🗂️ *Preços dos Grids:*\n"
                    + "\n".join([f"  • ${p}" for p in grids])
                )
                enviar_telegram(mensagem)
                status = "ALERTA ENVIADO"
                oportunidades.append({
                    "symbol": symbol,
                    "volatilidade": volatilidade,
                    "preco_min": preco_min,
                    "preco_max": preco_max
                })

            salvar_log([
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                symbol, preco_atual, high, low, f"{volatilidade:.2f}%",
                vol, rsi, macd_line, signal_line, status
            ])

            print(f"✅ [{symbol}] Log salvo - Status: {status}")

        except Exception as e:
            print(f"❌ Erro para {symbol}: {e}")

    return oportunidades


if __name__ == "__main__":
    last_summary_time = datetime.now(timezone.utc) - timedelta(hours=3)

    while True:
        oportunidades = main()

        agora = datetime.now(timezone.utc)
        if (agora - last_summary_time) >= timedelta(hours=3):
            resumo = gerar_resumo(oportunidades)
            enviar_telegram(resumo)
            last_summary_time = agora

        print("⏳ Aguardando 1 hora até o próximo ciclo...")
        time.sleep(3600)  # Espera 1 hora antes do próximo ciclo







