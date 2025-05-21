from flask import Flask, request, jsonify
import psycopg2
import os
from datetime import datetime
import telegram

app = Flask(__name__)

# Variáveis de ambiente
DATABASE_URL = os.environ.get("DATABASE_URL")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Telegram bot
bot = telegram.Bot(token=TELEGRAM_TOKEN)

@app.route("/webhook", methods=["POST"])
def receber_webhook():
    dados = request.json
    print(f"\U0001F4C4 Dados recebidos: {dados}")

    status = dados.get("data", {}).get("status")
    email = dados.get("data", {}).get("buyer", {}).get("email")

    print(f"[Webhook recebido] Status: {status} | Email: {email}")

    if email and status:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            timestamp = datetime.now()
            cursor.execute(
                "INSERT INTO compradores (email, status, timestamp) VALUES (%s, %s, %s)",
                (email, status, timestamp)
            )
            conn.commit()
            cursor.close()
            conn.close()

            # Envia mensagem para o Telegram
            if status.lower() in ["approved", "completed", "purchase_approved"]:
                mensagem = f"\u2705 Novo acesso aprovado: {email}"
            elif status.lower() in ["canceled", "refunded", "chargeback", "purchase_canceled"]:
                mensagem = f"\u26a0\ufe0f Acesso cancelado: {email}"
            else:
                mensagem = f"\ud83d\udcc8 Status desconhecido para: {email}"

            bot.send_message(chat_id=CHAT_ID, text=mensagem)

            return jsonify({"mensagem": "Dados salvos e mensagem enviada."}), 200

        except Exception as e:
            print(f"Erro ao salvar no banco ou enviar mensagem: {e}")
            return jsonify({"erro": "Falha ao processar."}), 500

    return jsonify({"erro": "Dados incompletos."}), 400

if __name__ == "__main__":
    app.run(debug=True)
