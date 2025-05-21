from flask import Flask, request, jsonify
import telegram
import os
import json
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Variáveis de ambiente (setadas no Render)
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
GSHEET_ID = os.environ['GSHEET_ID']
GOOGLE_CREDENTIALS_JSON = os.environ['GOOGLE_CREDENTIALS_JSON']

bot = telegram.Bot(token=TELEGRAM_TOKEN)

# Autenticando com o Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(GSHEET_ID).sheet1

@app.route('/webhook', methods=['POST'])
def receber_webhook():
    dados = request.json
    print("\U0001F4C4 Dados recebidos:", dados)

    status = dados.get("event")
    email = dados.get("buyer", {}).get("email", "None")

    print(f"\U0001F514 Webhook recebido | Status: {status} | Email: {email}")

    if status in ["PURCHASE_APPROVED", "PURCHASE_COMPLETED"]:
        mensagem = f"\u2705 Novo acesso aprovado: {email}\nBem-vindo ao grupo VIP!"
        bot.send_message(chat_id=CHAT_ID, text=mensagem)
        escrever_no_google_sheets(email, status)

    elif status in ["PURCHASE_CANCELED", "PURCHASE_REFUNDED", "CHARGEBACK"]:
        mensagem = f"\u26a0\ufe0f Acesso cancelado: {email}\nRemova do grupo manualmente se necessário."
        bot.send_message(chat_id=CHAT_ID, text=mensagem)
        escrever_no_google_sheets(email, status)

    return jsonify({"status": "recebido"}), 200

def escrever_no_google_sheets(email, status):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    sheet.append_row([agora, email, status])

if __name__ == "__main__":
    app.run(debug=True)
