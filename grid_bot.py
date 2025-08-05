import requests
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from datetime import datetime, timezone
import os
import time
import csv

# ======= CONFIGURAÇÕES ========

TELEGRAM_TOKEN = os.getenv("7702016556:AAEHotyy2l_TSM__loLKV9ZC7oo3duitJ8s")  # coloque seu token no env
CHAT_ID = os.getenv("2096206738")  # coloque seu chat_id no env

SYMBOLS = [
    "BTC-USDT", "ETH-USDT", "SOL-USDT", "ADA-USDT", "XRP-USDT",
    "DOGE-USDT", "AVAX-USDT", "DOT-USDT", "MATIC-USDT", "BNB-USDT",
    "LINK-USDT", "ATOM-USDT", "LTC-USDT", "BCH-USDT", "FIL-USDT",
    "AAVE-USDT", "NEAR-USDT", "SAND-USDT", "AXS-USDT", "APE-USDT",
    "RNDR-USDT", "FTM-USDT", "VET-USDT", "ICP-USDT", "HBAR-USDT"
]

NUM_GRIDS = 10
STOP_LOSS_PERCENT = 0.03
TAKE_PROFIT_PERCENT = 0.03
LOG_FILE = "log.csv"

CHECK_INTERVAL = 3600  # 1 hora em segundos
SUMMARY_INTERVAL = 10800  # 3 horas em segundos

# ======= FUNÇÕES ========

def get_market_data(symbol):
    url = f"https://api.kucoin.com/api/v1/market/stats?symbol={symbol}"
    response = requests.get(url)
    data = response.json()
    if data["code"] == "200000":
        return {
            "price": float(data["data"]["last"]),
            "high": float(data["data"]["high"]),
            "low": float(data["data"]["low"]),
            "vol": float(data["data"]["vol"])
        }
    else:
        return None

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
        return None

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
    print("Telegram response:", response.text)

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

def analisar_ativos():
    oportunidades = []

    for symbol in SYMBOLS:
        try:
            market_data = get_market_data(symbol)
            if market_data is None:
                print(f"Erro ao buscar dados de mercado para {symbol}")
                continue

            preco_atual = market_data["price"]
            high = market_data["high"]
            low = market_data["low"]
            vol = market_data["vol"]

            candles_df = get_candles(symbol)
            if candles_df is None or candles_df.isnull().values.any():
                print(f"Candles inválidos para {symbol}")
                continue

            rsi, macd_line, signal_line = calcular_indicadores(candles_df)

            preco_min, preco_max, volatilidade = calcular_faixa_grid(preco_atual, high, low)
            grids = calcular_precos_grids(preco_min, preco_max, NUM_GRIDS)
            stop_loss = preco_atual * (1 - STOP_LOSS_PERCENT)
            take_profit = preco_atual * (1 + TAKE_PROFIT_PERCENT)

            status = "SEM ALERTA"
            opportunity = False

            # FILTROS precisos
            if 0.01 <= volatilidade <= 0.08 and rsi < 40 and macd_line > signal_line:
                opportunity = True
                mensagem = (
                    f"*📊 Grid Bot PRO - SINAL GERADO!*\n"
                    f"🔹 *Par:* {symbol}\n"
                    f"💰 *Preço Atual:* ${preco_atual:.2f}\n"
                    f"📈 *Alta 24h:* ${high:.2f}\n"
                    f"📉 *Baixa 24h:* ${low:.2f}\n"
                    f"🌊 *Volatilidade:* {volatilidade*100:.2f}%\n"
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

            salvar_log([
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                symbol, preco_atual, high, low, f"{volatilidade*100:.2f}%",
                vol, rsi, macd_line, signal_line, status
            ])

            if opportunity:
                oportunidades.append({
                    "symbol": symbol,
                    "price": preco_atual,
                    "volatility": volatilidade*100,
                    "rsi": rsi,
                    "macd": macd_line,
                    "signal": signal_line,
                    "grid_min": preco_min,
                    "grid_max": preco_max,
                    "num_grids": NUM_GRIDS,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit
                })

            print(f"✅ [{symbol}] Status: {status}")

        except Exception as e:
            print(f"❌ Erro para {symbol}: {e}")

    return oportunidades

def enviar_resumo(oportunidades):
    if not oportunidades:
        print("Nenhuma oportunidade para resumo.")
        return

    mensagem = "*⏰ RESUMO DAS MELHORES OPORTUNIDADES (Últimas 3h)*\n\n"
    for opp in oportunidades:
        mensagem += (
            f"📊 *{opp['symbol']}* | RSI: {opp['rsi']:.2f} | Vol: {opp['volatility']:.2f}% | "
            f"Preço: ${opp['price']:.2f} | Grid: ${opp['grid_min']:.2f} - ${opp['grid_max']:.2f} | "
            f"Grids: {opp['num_grids']} | SL: ${opp['stop_loss']:.2f} | TP: ${opp['take_profit']:.2f}\n"
        )

    enviar_telegram(mensagem)

# ======= EXECUÇÃO ========

if __name__ == "__main__":
    start_time = time.time()
    resumo_oportunidades = []

    while True:
        ciclo_start = time.time()

        # Analisar ativos e enviar alertas individuais
        oportunidades = analisar_ativos()
        resumo_oportunidades.extend(oportunidades)

        # Se passaram 3 horas desde último resumo, envia resumo e limpa lista
        if ciclo_start - start_time >= SUMMARY_INTERVAL:
            enviar_resumo(resumo_oportunidades)
            resumo_oportunidades = []
            start_time = ciclo_start

        print(f"⏳ Próximo ciclo em {CHECK_INTERVAL/60:.0f} minutos...")
        time.sleep(CHECK_INTERVAL)










