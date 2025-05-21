from flask import Flask, request, jsonify
import telegram
import os
import csv
import time
from datetime import datetime
import gspread
from google.oauth2 import service_account
import json

app = Flask(__name__)

# Configurações
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

bot = telegram.Bot(token=TELEGRAM_TOKEN)

# Autenticação com Google Sheets
credentials_str = os.getenv("GOOGLE_CREDENTIALS_JSON")
credentials_dict = json.loads(credentials_str)

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
credentials_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
creds = service_account.Credentials.from_service_account_info(credentials_dict, scopes=scopes)
client = gspread.authorize(creds)
sheet = client.open_by_key(GOOGLE_SHEET_ID).worksheet("aprovados")

@app.route('/webhook', methods=['POST'])
def receber_webhook():
    dados = request.json
    print(f"📦 Dados recebidos: {dados}")

    # Extrair dados principais
    event = dados.get("event")
    email = dados.get("buyer", {}).get("email", "Desconhecido")
    status = dados.get("data", {}).get("status", event)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"⚠️ Webhook recebido | Status: {status} | Email: {email}")

    # Registrar no Google Sheets
    try:
        sheet.append_row([timestamp, email, status])
        print("✅ Registro adicionado ao Google Sheets.")
    except Exception as e:
        print(f"Erro ao escrever na planilha: {e}")

    # Enviar mensagem no grupo
    if status in ["PURCHASE_APPROVED", "APPROVED", "COMPLETED"]:
        msg = f"✅ Novo acesso aprovado: {email}\nBem-vindo ao grupo VIP!"
    elif status in ["PURCHASE_CANCELED", "CANCELED", "REFUNDED", "CHARGEBACK"]:
        msg = f"⚠️ Acesso cancelado: {email}\nRemova do grupo manualmente se necessário."
    else:
        msg = f"📩 Status recebido: {status} | Email: {email}"

    try:
        bot.send_message(chat_id=CHAT_ID, text=msg)
        print("✅ Mensagem enviada para o Telegram.")
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(debug=True)
