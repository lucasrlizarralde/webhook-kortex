import os
import threading
from datetime import datetime
from flask import Flask, request, jsonify
import psycopg2
import telegram
import smtplib
from email.message import EmailMessage
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
from telegram import Update

# === Configuração das variáveis de ambiente ===
DATABASE_URL        = os.environ['DATABASE_URL']
TELEGRAM_TOKEN      = os.environ['TELEGRAM_TOKEN']
ADMIN_CHAT_ID       = int(os.environ['ADMIN_CHAT_ID'])   # Seu chat ID pessoal
GROUP_CHAT_ID       = int(os.environ['GROUP_CHAT_ID'])   # ID do grupo VIP
FROM_EMAIL          = os.environ['FROM_EMAIL']
FROM_EMAIL_PASSWORD = os.environ['FROM_EMAIL_PASSWORD']

# === Flask App para Webhook ===
app = Flask(__name__)
bot = telegram.Bot(token=TELEGRAM_TOKEN)

def enviar_email(destinatario: str):
    msg = EmailMessage()
    msg['Subject'] = 'Acesso ao grupo VIP'
    msg['From']    = FROM_EMAIL
    msg['To']      = destinatario
    msg.set_content(
        'Olá! 👋\n\n' 
        'Parabéns pela sua compra!\n\n'
        'Para acessar o grupo VIP, inicie uma conversa com o bot: https://t.me/{}\n'
        'Envie o e-mail usado na compra para gerar seu link de acesso exclusivo.\n\n'
        'Abraços,\nEquipe Kortex Signals'.format(bot.username)
    )
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(FROM_EMAIL, FROM_EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f'✅ E-mail enviado para {destinatario}')
    except Exception as e:
        print(f'❌ Falha ao enviar e-mail para {destinatario}: {e}')

@app.route('/webhook', methods=['POST'])
def webhook():
    dados = request.get_json(force=True, silent=True)
    print('📄 Webhook recebido:', dados)
    purchase = dados.get('data', {}).get('purchase', {})
    status   = purchase.get('status')
    buyer    = dados.get('data', {}).get('buyer', {})
    email    = buyer.get('email')

    # Registra no banco
    if email and status:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur  = conn.cursor()
            cur.execute(
                "INSERT INTO compradores (email, status, timestamp) VALUES (%s, %s, %s)",
                (email, status, datetime.now())
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f'❌ Erro no DB: {e}')

        # Notifica admin
        text = f'✅ Compra {status.lower()}: {email}' if status.lower() in ('approved','completed','purchase_approved') else f'⚠️ {status.lower()}: {email}'
        bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
        print(f'📬 Notificação enviada ao admin: {text}')

        # Envia e-mail automático
        if status.lower() in ('approved','completed','purchase_approved'):
            threading.Thread(target=enviar_email, args=(email,)).start()

    return jsonify({'status':'ok'}), 200

# === Bot de Conversa para convite ===
EMAIL = 0

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Olá! 👋\nEnvie o e-mail que você usou na compra para verificar seu acesso ao grupo VIP.'
    )
    return EMAIL

def receber_email(update: Update, context: CallbackContext) -> int:
    email_usuario = update.message.text.strip().lower()
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur  = conn.cursor()
        cur.execute(
            "SELECT status FROM compradores WHERE email=%s ORDER BY timestamp DESC LIMIT 1", (email_usuario,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row and row[0].lower() in ('approved','completed','purchase_approved'):
            invite = bot.create_chat_invite_link(
                chat_id=GROUP_CHAT_ID,
                expire_date=int(datetime.now().timestamp())+600,
                member_limit=1
            )
            update.message.reply_text(
                f'✅ Acesso confirmado!\nAqui está seu link exclusivo (10 min / 1 uso):\n{invite.invite_link}'
            )
        else:
            update.message.reply_text(
                '❌ E-mail não aprovado ou não encontrado.\n' 
                'Entre em contato com o suporte.'
            )
    except Exception as e:
        print(f'❌ Erro ao processar convite: {e}')
        update.message.reply_text('❌ Erro interno. Tente mais tarde.')
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Conversa cancelada. Use /start para recomeçar.')
    return ConversationHandler.END

# === Execução Conjunta ===
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

def main():
    # Inicia Flask em thread separada
    threading.Thread(target=run_flask).start()

    # Inicia bot polling
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={EMAIL: [MessageHandler(Filters.text & ~Filters.command, receber_email)]},
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(conv)
    print('🤖 Bot de convite iniciado.')
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
