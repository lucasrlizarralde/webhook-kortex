from flask import Flask, request, jsonify
import telegram
import os

app = Flask(__name__)

# 🔐 Token e chat ID puxados de variáveis de ambiente
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = telegram.Bot(token=TELEGRAM_TOKEN)

@app.route('/webhook', methods=['POST'])
def receber_webhook():
    dados = request.json

    status = dados.get("status")
    email = dados.get("buyer", {}).get("email", "Desconhecido")

    print(f"[🔔 Webhook recebido] Status: {status} | Email: {email}")

    if status in ["approved", "completed"]:
        mensagem = f"✅ Novo acesso aprovado: {email}\nBem-vindo ao grupo VIP!"
        bot.send_message(chat_id=CHAT_ID, text=mensagem)

    elif status in ["canceled", "refunded", "chargeback"]:
        mensagem = f"⚠️ Acesso cancelado: {email}\nRemova do grupo manualmente se necessário."
        bot.send_message(chat_id=CHAT_ID, text=mensagem)

    return jsonify({"status": "recebido"}), 200

if __name__ == "__main__":
    app.run(debug=True)
