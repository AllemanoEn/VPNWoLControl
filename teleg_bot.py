import logging
import subprocess
import json

from pathlib import Path
from datetime import datetime

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    filters
)

import SECRETS
import AUTHORIZED_USERNAMES


# -----------------------------------------------------------------------------
# Logging configuration
# -----------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Constants / Files
# -----------------------------------------------------------------------------

PLEX_STATE_FILE = Path("plex_state.json")


# -----------------------------------------------------------------------------
# Plex state file helpers
# -----------------------------------------------------------------------------

def ensure_plex_state_file() -> None:
    """
    Ensure that the Plex state file exists.

    If the file does not exist, it is created with an empty list.
    The file stores the full history of Plex start events.
    """
    if not PLEX_STATE_FILE.exists():
        with open(PLEX_STATE_FILE, "w") as f:
            json.dump([], f)
        logger.info("Created plex_state.json file")


def save_plex_start(user: dict) -> None:
    """
    Save a Plex start event to the history file.

    The event is inserted at the beginning of the list so the most
    recent entries are always first.

    Args:
        user (dict): Telegram user object who triggered the Plex start.
    """
    try:
        if PLEX_STATE_FILE.exists():
            with open(PLEX_STATE_FILE) as f:
                data = json.load(f)
            if not isinstance(data, list):
                data = []
        else:
            data = []
    except (json.JSONDecodeError, IOError):
        logger.warning("Invalid plex_state.json, resetting file")
        data = []

    entry = {
        "username": user.get("username") or "sans_username",
        "user_id": user.get("id"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    data.insert(0, entry)

    with open(PLEX_STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)

    logger.info("Plex start saved: %s (%s)", entry["username"], entry["user_id"])


def load_plex_start() -> list:
    """
    Load the Plex start history from disk.

    Returns:
        list: List of Plex start events (may be empty).
    """
    try:
        with open(PLEX_STATE_FILE) as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return []


# -----------------------------------------------------------------------------
# Network helpers
# -----------------------------------------------------------------------------

def is_host_up(ip: str) -> bool:
    """
    Check if a host is reachable via ICMP ping.

    Args:
        ip (str): IP address to test.

    Returns:
        bool: True if host responds to ping, False otherwise.
    """
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except Exception as exc:
        logger.error("Ping failed: %s", exc)
        return False


# -----------------------------------------------------------------------------
# Telegram command handlers
# -----------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /start command handler.
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hello, c'est le BOT pour contrôler le serveur Plex ✨"
    )


async def okay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /okay command handler (basic connectivity test).
    """
    logger.info("Okay command received")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Commande bien reçue !"
    )


async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /whoami command handler.

    Displays the Telegram username and user ID.
    """
    user = update.message.from_user
    logger.info("whoami called by %s (%s)", user.username, user.id)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Tu es {user.username} et ton ID est : {user.id}"
    )


async def statut(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /statut command handler.

    Checks whether the Plex server is currently reachable.
    """
    if is_host_up(SECRETS.PLEX_IP):
        msg = "Le serveur Plex est allumé ⚡"
    else:
        msg = "Le serveur Plex est éteint 🔌"

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=msg
    )


async def switch_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /switch_on command handler.

    Sends a Wake-on-LAN packet to the Plex server and logs the user
    who initiated the action.
    """
    user = update.message.from_user
    logger.info("/switch_on triggered by %s", user.username)

    subprocess.run(
        ["sudo", "etherwake", "-i", "eno1", SECRETS.PLEX_MAC_ADDRESS],
        capture_output=True
    )

    save_plex_start(user)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Le serveur Plex va démarrer (attendre ~20 sec) ✅⏳"
    )


async def switch_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /switch_off command handler.

    Currently informational only.
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Le serveur Plex va s'éteindre 🔌"
    )


async def plex_last_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /plex_last_start command handler.

    Displays the three most recent Plex start events.
    """
    data = load_plex_start()

    if not data:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Aucun démarrage de Plex enregistré."
        )
        return

    last_three = data[:3]

    msg = "📺 *Trois derniers démarrages Plex*\n\n"
    for i, entry in enumerate(last_three, start=1):
        msg += (
            f"{i}. 👤 `{entry['username']}`\n"
            f"   🆔 `{entry['user_id']}`\n"
            f"   🕒 {entry['timestamp']}\n\n"
        )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=msg,
        parse_mode="Markdown"
    )


# -----------------------------------------------------------------------------
# Application bootstrap
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    ensure_plex_state_file()

    application = ApplicationBuilder().token(
        SECRETS.TELEGRAM_BOT_TOKEN
    ).build()

    auth_filter = filters.User(
        username=AUTHORIZED_USERNAMES.AUTHORIZED_USERNAMES_LIST
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("okay", okay))
    application.add_handler(CommandHandler("whoami", whoami))
    application.add_handler(CommandHandler("statut", statut, auth_filter))
    application.add_handler(CommandHandler("switch_on", switch_on, auth_filter))
    application.add_handler(CommandHandler("switch_off", switch_off, auth_filter))
    application.add_handler(CommandHandler("plex_last_start", plex_last_start, auth_filter))

    application.run_polling()
