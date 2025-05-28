import logging
import subprocess
import SECRETS
import AUTHORIZED_USERNAMES

from datetime import datetime

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters

'''
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
'''

def is_host_up(ip: str) -> bool:
    try:
        output = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return output.returncode == 0
    except Exception:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello, c'est le BOT pour contrôler le serveur Plex ✨")

async def okay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Okay command received!")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Commande bien reçue !")
    
async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    print('You talk with user {} and his user ID: {} '.format(user['username'], user['id']))
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Tu es {} et ton ID est : {} '.format(user['username'], user['id']))
    
async def statut(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_host_up(SECRETS.PLEX_IP):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Le serveur Plex est allumé ⚡")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Le serveur Plex est éteint 🔌")

async def switch_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(subprocess.run(["sudo", "etherwake", "-i", "eth0", SECRETS.PLEX_MAC_ADDRESS], 
                     capture_output=True))
    
    user = update.message.from_user
    print('{} - User {} start the server !\n'.format(datetime.now() ,user['username'])) 
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Le serveur Plex va démarrer (attendre ~20 sec) ✅⏳")
    
async def switch_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Le serveur Plex va s'éteindre 🔌")

if __name__ == '__main__':
    token = SECRETS.TELEGRAM_BOT_TOKEN
    if not token:
        raise ValueError("No TELEGRAM_BOT_TOKEN set in config.py")

    application = ApplicationBuilder().token(token).build()

    start_handler = CommandHandler('start', start)
    okay_handler = CommandHandler('okay', okay)
    whoami_handler = CommandHandler('whoami', whoami)
    statut_handler = CommandHandler('statut', statut, filters.User(username=AUTHORIZED_USERNAMES.AUTHORIZED_USERNAMES_LIST))
    switch_on_handler = CommandHandler('switch_on', switch_on, filters.User(username=AUTHORIZED_USERNAMES.AUTHORIZED_USERNAMES_LIST))
    switch_off_handler = CommandHandler('switch_off', switch_off, filters.User(username=AUTHORIZED_USERNAMES.AUTHORIZED_USERNAMES_LIST))

    application.add_handler(start_handler)
    application.add_handler(okay_handler)
    application.add_handler(whoami_handler)
    application.add_handler(statut_handler)
    application.add_handler(switch_on_handler)
    application.add_handler(switch_off_handler)

    application.run_polling()
