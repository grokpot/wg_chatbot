import datetime
import logging
import os
import pytz
import random
import threading

from telegram import Update
from telegram.ext import (
    Updater,
    MessageHandler,
    Filters,
    CallbackContext,
)

"""
DOCS
https://core.telegram.org/bots
https://python-telegram-bot.readthedocs.io/en/stable/telegram.ext.jobqueue.html
https://medium.com/analytics-vidhya/python-telegram-bot-with-scheduled-tasks-932edd61c534
https://towardsdatascience.com/how-to-deploy-a-telegram-bot-using-heroku-for-free-9436f89575d2
https://nullonerror.org/2021/01/08/hosting-telegram-bots-on-google-cloud-run/
"""

# ENV Vars
PORT = os.environ.get("PORT")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_DEV_CHAT_ID = os.environ.get("TELEGRAM_DEV_CHAT_ID")
TELEGRAM_WG_CHAT_ID = os.environ.get("TELEGRAM_WG_CHAT_ID")
GITHUB_COMMIT_SHA = os.environ.get("GITHUB_COMMIT_SHA", "local testing SHA")
GITHUB_COMMIT_MESSAGE = os.environ.get("GITHUB_COMMIT_MESSAGE", "local testing message")

# ENUMs
GREETING_LIST = [
    "Tschau!",
    "Ciao!",
    "Liebe Lieben,",
    "Servus!",
    "Habediehre!",
    "Sehr Geehrte Herren,",
]
GOODBYE_LIST = [
    "Tschau!",
    "Ciao!",
    "Tschüss!",
    "Tschüssli!",
    "MfG,",
    "LG,",
    "Adios!",
    "さよなら!",
]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_random_greeting():
    return random.choice(GREETING_LIST)


def get_random_goodbye():
    return random.choice(GOODBYE_LIST)


def build_message(body, signature):
    return "\n".join([get_random_greeting(), body, get_random_goodbye(), signature])


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)


class Sennbot:
    signature = "🤖 Sennbot"

    def __init__(self):
        self.updater = Updater(token=TELEGRAM_BOT_TOKEN)
        dispatcher = self.updater.dispatcher
        dispatcher.add_handler(
            MessageHandler(Filters.text & ~Filters.command, self.message_receive)
        )
        cron = self.updater.job_queue
        tz = pytz.timezone("Europe/Zurich")

        # Announce new deployment in testing chat
        self.message_send_new_deployment()

        # Trash
        # Every Wednesday, Sunday at 21:00
        cron.run_daily(
            self.message_send_reminder_trash,
            days=[2, 6],
            time=datetime.time(
                hour=20, minute=45, second=00, tzinfo=tz
            ),
        )
        # Paper
        # Every 2 weeks at 20:30
        cron.run_repeating(
            self.message_send_reminder_paper, 
            interval=datetime.timedelta(weeks=2), 
            first=datetime.datetime(2021, 10, 12, 20, 30, tzinfo=tz)
        )
        # Recycling
        # Sämi wants it every Thursday at 11
        cron.run_daily(
            self.message_send_reminder_recycling,
            days=[3],
            time=datetime.time(
                hour=11, minute=00, second=00, tzinfo=tz
            ),
        )
        # Finances
        # Ryan wants it every month on the 7th at 17:00
        cron.run_monthly(
            self.message_send_reminder_finances,
            when=datetime.time(hour=17, tzinfo=tz),
            day=7
        )

        logger.info("Sennbot Started")
        self.updater.start_polling(drop_pending_updates=True)
        self.updater.idle()

    def message_receive(self, update: Update, context: CallbackContext) -> None:
        """
        Handles incoming messages
        """
        incoming_message = update.message.text.lower()

        # Only execute when messages begin with "bot"
        if len(incoming_message) >= 3 and incoming_message[:3] != "bot":
            return

        if 'identify' in incoming_message:
            incoming_chat_id = update.effective_chat.id
            message = build_message(
                f"This chat ID: {incoming_chat_id}",
                self.signature,
            )
            context.bot.send_message(chat_id=incoming_chat_id, text=message)
        
        else:
            echo(update, context)

    def message_send_new_deployment(self):
        self.send_test_message(f"New Deployment\n SHA: {GITHUB_COMMIT_SHA}\n Message: {GITHUB_COMMIT_MESSAGE}")

    def message_send_reminder_trash(self, context):
        message = build_message("Morn isch Mülltag.", self.signature)
        self.send_wg_message(message)

    def message_send_reminder_paper(self, context):
        message = build_message("Morn isch Karton-Recycling Tag.", self.signature)
        self.send_wg_message(message)

    def message_send_reminder_recycling(self, context):
        message = build_message("Bitte denk an das Recycling.", self.signature)
        self.send_wg_message(message)

    def message_send_reminder_finances(self, context):
        message = build_message("Ryan sollte die Finanzen regeln. Überprüfe Splitwise auf ausstehende Beträge.", self.signature)
        self.send_wg_message(message)

    def send_test_message(self, message):
        """
        Sends a message to the Test Chat
        """
        self.updater.bot.send_message(chat_id=TELEGRAM_DEV_CHAT_ID, text=message)

    def send_wg_message(self, message):
        """
        Sends a message to the WG Chat
        """
        self.updater.bot.send_message(chat_id=TELEGRAM_WG_CHAT_ID, text=message)


if __name__ == "__main__":
    Sennbot()
