import logging
import SECRETS
import AUTHORIZED_USERNAMES
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello, c'est le BOT pour contrôler le serveur Plex ✨")

async def okay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Okay command received!")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Okay command received!")
    
async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    print('You talk with user {} and his user ID: {} '.format(user['username'], user['id']))

if __name__ == '__main__':
    token = SECRETS.TELEGRAM_BOT_TOKEN
    if not token:
        raise ValueError("No TELEGRAM_BOT_TOKEN set in config.py")

    application = ApplicationBuilder().token(token).build()

    start_handler = CommandHandler('start', start)
    okay_handler = CommandHandler('okay', okay)
    whoami_handler = CommandHandler('whoami', whoami, filters.User(username=AUTHORIZED_USERNAMES.AUTHORIZED_USERNAMES_LIST))

    application.add_handler(start_handler)
    application.add_handler(okay_handler)
    application.add_handler(whoami_handler)

    application.run_polling()
