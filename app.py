from flask import Flask, request, jsonify
import psycopg2
import os
from datetime import datetime
import telegram
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

# Variáveis de ambiente
DATABASE_URL = os.environ.get("DATABASE_URL")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
FROM_EMAIL = os.environ.get("FROM_EMAIL")
FROM_EMAIL_PASSWORD = os.environ.get("FROM_EMAIL_PASSWORD")

# Telegram bot
bot = telegram.Bot(token=TELEGRAM_TOKEN)

def enviar_email_para_cliente(destinatario):
    msg = EmailMessage()
    msg["Subject"] = "Acesso ao grupo VIP"
    msg["From"] = FROM_EMAIL
    msg["To"] = destinatario
    msg.set_content(
        "Olá! 👋\n\nParabéns pela sua compra!\n\nPara acessar o grupo VIP, fale com nosso bot clicando neste link: https://t.me/SeuBotUsername\n\nDepois, envie seu e-mail para validação.\n\nEsse link é exclusivo para você. Não compartilhe.\n\nAbraços,\nEquipe Kortex Signals"
    )

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(FROM_EMAIL, FROM_EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ E-mail enviado para {destinatario}")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")

@app.route("/webhook", methods=["POST"])
def receber_webhook():
    dados = request.get_json(force=True, silent=True)
    print(f"📄 Dados recebidos: {dados}")

    # Extração correta para Hotmart subscription webhook
    purchase = dados.get("data", {}).get("purchase", {})
    status = purchase.get("status")
    email = dados.get("data", {}).get("buyer", {}).get("email")

    print(f"[Webhook recebido] Status: {status} | Email: {email}")

    if email and status:
        try:
            # Salva no banco Neon
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

            # Decide mensagem e ações
            status_lower = status.lower()
            if status_lower in ["approved", "completed", "purchase_approved"]:
                mensagem = f"✅ Novo acesso aprovado: {email}"
                enviar_email_para_cliente(email)
            elif status_lower in ["canceled", "refunded", "chargeback", "purchase_canceled"]:
                mensagem = f"⚠️ Acesso cancelado: {email}"
            else:
                mensagem = f"📈 Status não tratado: {status} para {email}"

            # Envia notificação no Telegram
            bot.send_message(chat_id=CHAT_ID, text=mensagem)
            print(f"📬 Mensagem Telegram enviada: {mensagem}")

            return jsonify({"mensagem": "Processado com sucesso."}), 200

        except Exception as e:
            print(f"❌ Erro ao processar webhook: {e}")
            return jsonify({"erro": "Falha ao processar."}), 500

    return jsonify({"erro": "Dados incompletos."}), 400

if __name__ == "__main__":
    app.run(debug=True)
