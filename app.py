from flask import Flask, request, jsonify
import telegram
import os
import csv
import time

app = Flask(__name__)

# Variáveis de ambiente (coloque essas no Render)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

bot = telegram.Bot(token=TELEGRAM_TOKEN)

@app.route("/webhook", methods=["POST"])
def receber_webhook():
    dados = request.json
    print("📦 Webhook recebido:", dados)

    status = dados.get("event")
    email = dados.get("data", {}).get("buyer", {}).get("email", "Desconhecido")

    print(f"[🔔 Webhook recebido] Status: {status} | Email: {email}")

    if status in ["PURCHASE_APPROVED", "PURCHASE_COMPLETED"]:
        # ✅ Gravar e-mail aprovado em CSV
        try:
            with open("aprovados.csv", mode="a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([email])
            print(f"📥 E-mail salvo: {email}")
        except Exception as e:
            print(f"❌ Erro ao salvar CSV: {e}")

        # Mensagem de log no grupo/admin
        mensagem = f"✅ Compra aprovada para: {email}\nSalvo no CSV para verificação futura."
        bot.send_message(chat_id=CHAT_ID, text=mensagem)

    elif status in ["PURCHASE_CANCELED", "PURCHASE_REFUNDED", "CHARGEBACK"]:
        mensagem = f"⚠️ Compra cancelada/reembolsada para: {email}"
        bot.send_message(chat_id=CHAT_ID, text=mensagem)

    return jsonify({"status": "recebido"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
