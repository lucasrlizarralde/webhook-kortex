from flask import Flask, request, jsonify
import telegram

app = Flask(__name__)

# 🔐 Seu token do Bot (cole aqui)
TELEGRAM_TOKEN = "7652361224:AAELGSnyobiX9URSMD7Pg-SQOCYhe2t-YRw"
CHAT_ID = "-1002510597155"
bot = telegram.Bot(token=TELEGRAM_TOKEN)

@app.route('/webhook', methods=['POST'])
def receber_webhook():
    dados = request.json

    status = dados.get("status")
    email = dados.get("buyer", {}).get("email", "Desconhecido")

    print(f"[🔔 Webhook recebido] Status: {status} | Email: {email}")

    # ✅ Se a compra for aprovada
    if status in ["approved", "completed"]:
        mensagem = f"✅ Novo acesso aprovado: {email}\nBem-vindo ao grupo VIP!"
        bot.send_message(chat_id=CHAT_ID, text=mensagem)
        # (aqui você pode enviar link privado, ou usar o método add_chat_member com user_id se tiver)

    # ❌ Se a compra foi cancelada, reembolsada ou teve chargeback
    elif status in ["canceled", "refunded", "chargeback"]:
        mensagem = f"⚠️ Acesso cancelado: {email}\nRemova do grupo manualmente se necessário."
        bot.send_message(chat_id=CHAT_ID, text=mensagem)

    return jsonify({"status": "recebido"}), 200

if __name__ == "__main__":
    app.run(debug=True)
