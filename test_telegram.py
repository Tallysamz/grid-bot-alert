import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

mensagem = "🔔 Teste de envio via bot Telegram!"

url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
data = {"chat_id": CHAT_ID, "text": mensagem}

res = requests.post(url, data=data)
print(f"Status code: {res.status_code}")
print(f"Response: {res.text}")
