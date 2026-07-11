import os
import logging
from flask import Flask
from threading import Thread
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, 
    ContextTypes, ConversationHandler
)

# --- WEB SERVER (To keep it awake) ---
app_server = Flask(__name__)
@app_server.route('/')
def home():
    return "Bot is alive!"

def run_web_server():
    app_server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# --- BOT LOGIC ---
TOKEN = '8941926536:AAFQgl0vpk16eJTrLaSDuoFOjLMyHAogrI8'
ADMIN_IDS = [1411115615, 8859978464]
CHOOSING, DEPOSIT_INSTRUCTION, UPLOADING = range(3)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def forward_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or update.effective_user.id in ADMIN_IDS:
        return
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.forward_message(chat_id=admin_id, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
        except Exception as e:
            logging.error(f"Forwarding failed: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await forward_all_messages(update, context)
    reply_keyboard = [['Vantage', 'XM']]
    await update.message.reply_text("Welcome! Please choose a platform:", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return CHOOSING

async def choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await forward_all_messages(update, context)
    user_choice = update.message.text
    if user_choice == 'Vantage':
        steps = "📌 If you already have a Vantage account:\nGo to: Dashboard → Profile → Change IB\nEnter IB / Rebate Code: 27867969"
    elif user_choice == 'XM':
        steps = "📌 If you already have a XM account? Follow these steps:\n•Go to: Dashboard → Profile → Click '+' icon (after your # ID)\n•Add new standard account→ choose MT5→ Use my partner code: GBVJB\n•After opening, go to 'manage' → do internal transfer of funds (0 fees)"
    else:
        await update.message.reply_text("Sorry the input is invalid")
        return CHOOSING
    
    context.user_data['platform'] = user_choice
    await update.message.reply_text(f"{steps}\n\nTo proceed, you must deposit a minimum of 100 USD. Please reply 'OK' to confirm.")
    return DEPOSIT_INSTRUCTION

async def deposit_ack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await forward_all_messages(update, context)
    if update.message.text.upper() == 'OK':
        await update.message.reply_text("Please upload a screenshot of your deposit where the account ID is clearly visible.")
        return UPLOADING
    await update.message.reply_text("Sorry the input is invalid")
    return DEPOSIT_INSTRUCTION

async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await forward_all_messages(update, context)
    if update.message.photo or update.message.document:
        await update.message.reply_text("Thank you for enrolling with us 😊. Please fill this form: https://forms.gle/XY3QQGosPehAkK6M6")
        return ConversationHandler.END
    await update.message.reply_text("Sorry the input is invalid")
    return UPLOADING

if __name__ == '__main__':
    # 1. Run web server in background
    Thread(target=run_web_server).start()
    
    # 2. Run Bot
    app_bot = ApplicationBuilder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choice)],
            DEPOSIT_INSTRUCTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_ack)],
            UPLOADING: [MessageHandler(filters.PHOTO | filters.Document.ALL, upload),
                        MessageHandler(filters.TEXT & ~filters.COMMAND, upload)]
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )
    app_bot.add_handler(conv_handler)
    app_bot.run_polling()