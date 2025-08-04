import os
import requests
import time
from datetime import datetime, timedelta

# ============ CONFIG =============
API_URL = "https://api.kucoin.com/api/v1/market/stats?symbol={symbol}"
LISTA_ATIVOS = [
    "BTC-USDT", "ETH-USDT", "SOL-USDT", "AVAX-USDT", "NEAR-USDT",
    "INJ-USDT", "RNDR-USDT", "TIA-USDT", "PYTH-USDT", "AR-USDT",
    "APE-USDT", "BLUR-USDT", "LDO-USDT", "MANTA-USDT", "SUI-USDT",
    "SEI-USDT", "HOOK-USDT", "GMT-USDT", "RAY-USDT", "ID-USDT"
]

VOL_MIN = 3.5  # volatilidade mínima (%)
VOLUME_NEGOCIO_MIN = 1_000_000  # volume mínimo em USDT
LIMITE_GRID = 10  # número de grids

CHAT_ID = os.getenv("CHAT_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

last_summary_time = datetime.now() - timedelta(hours=3)

# ============ FUNÇÕES =============
def enviar_mensagem_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")

def buscar_dados(symbol):
    try:
        url = API_URL.format(symbol=symbol)
        r = requests.get(url)
        data = r.json()["data"]
        return {
            "simbolo": symbol,
            "preco": float(data["last"]),
            "volatilidade": abs(float(data["changeRate"])) * 100,
            "volume": float(data["volValue"]),
        }
    except:
        return None

def analisar_cripto(symbol):
    dados = buscar_dados(symbol)
    if not dados:
        return None

    faixa = dados["preco"] * dados["volatilidade"] / 100
    dados.update({
        "faixa_min": round(dados["preco"] - faixa, 4),
        "faixa_max": round(dados["preco"] + faixa, 4),
        "grids": LIMITE_GRID,
        "stop_loss": round(dados["preco"] * 0.85, 4),
        "trailing_stop": 3
    })
    return dados

def passou_nos_filtros(dados):
    return (
        dados["volatilidade"] >= VOL_MIN
        and dados["volume"] >= VOLUME_NEGOCIO_MIN
    )

def enviar_alerta_telegram(dados):
    msg = (
        f"🚨 <b>Oportunidade Detectada!</b> 🚨\n"
        f"<b>Cripto:</b> {dados['simbolo']}\n"
        f"<b>Preço Atual:</b> {dados['preco']}\n"
        f"<b>Volatilidade:</b> {dados['volatilidade']}%\n"
        f"<b>Volume 24h:</b> {round(dados['volume']):,} USDT\n"
        f"<b>Faixa de Grid:</b> {dados['faixa_min']} - {dados['faixa_max']}\n"
        f"<b>Grids:</b> {dados['grids']}\n"
        f"<b>Stop Loss:</b> {dados['stop_loss']}\n"
        f"<b>Trailing Stop:</b> {dados['trailing_stop']}%"
    )
    enviar_mensagem_telegram(msg)

def gerar_resumo(lista):
    if not lista:
        return "Nenhuma oportunidade identificada nas últimas 3 horas."

    resumo = ""
    for c in lista:
        resumo += (
            f"📈 {c['simbolo']} | Vol: {c['volatilidade']}%\n"
            f"💰 Faixa: {c['faixa_min']} - {c['faixa_max']}\n"
            f"🔢 Grids: {c['grids']}\n\n"
        )
    return resumo

# ============ LOOP PRINCIPAL =============
while True:
    oportunidades = []

    for ativo in LISTA_ATIVOS:
        dados = analisar_cripto(ativo)
        if dados and passou_nos_filtros(dados):
            oportunidades.append(dados)
            enviar_alerta_telegram(dados)

    agora = datetime.now()
    if agora - last_summary_time >= timedelta(hours=3):
        resumo = gerar_resumo(oportunidades)
        enviar_mensagem_telegram(f"🕒 <b>RESUMO DAS ÚLTIMAS 3 HORAS:</b>\n\n{resumo}")
        last_summary_time = agora

    time.sleep(60 * 60)  # Executa a cada 1h






