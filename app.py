from flask import Flask, request, jsonify
import telegram
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# 🔐 Variáveis de ambiente (configure no Render)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON")
SHEET_ID = "103NQ-SW3jaY5V4lrjmUj2UBaPRBvgLeFrd_4STtMAnk"

bot = telegram.Bot(token=TELEGRAM_TOKEN)

def salvar_dados_na_planilha(data, evento, email):
    try:
        # Autenticação com a conta de serviço
        creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # Acessa a planilha e aba padrão (primeira aba)
        sheet = client.open_by_key(SHEET_ID).sheet1

        # Salva a linha com data, status e e-mail
        sheet.append_row([data, evento, email])
        print(f"✅ Dados salvos na planilha: {email}")

    except Exception as e:
        print(f"❌ Erro ao salvar no Google Sheets: {e}")

@app.route("/webhook", methods=["POST"])
def receber_webhook():
    dados = request.json
    print("📦 Webhook recebido:", dados)

    status = dados.get("event")
    email = dados.get("data", {}).get("buyer", {}).get("email", "Desconhecido")

    print(f"[🔔 Webhook recebido] Status: {status} | Email: {email}")

    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 🎯 Apenas se a compra foi aprovada
    if status in ["PURCHASE_APPROVED", "PURCHASE_COMPLETED"]:
        salvar_dados_na_planilha(data, status, email)

        mensagem = f"✅ Compra aprovada para: {email}\nAcesso registrado."
        bot.send_message(chat_id=CHAT_ID, text=mensagem)

    elif status in ["PURCHASE_CANCELED", "PURCHASE_REFUNDED", "CHARGEBACK"]:
        mensagem = f"⚠️ Compra cancelada/reembolsada para: {email}"
        bot.send_message(chat_id=CHAT_ID, text=mensagem)

    return jsonify({"status": "recebido"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
