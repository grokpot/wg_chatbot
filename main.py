from asyncio import CancelledError
import datetime
import logging
import os
import pytz
import random
from urllib.parse import urlparse

import redis
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    CallbackContext,
    filters,
    MessageHandler,
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
LOCAL = os.environ.get("LOCAL", False)
if LOCAL:
    from dotenv import load_dotenv

    load_dotenv()
PORT = os.environ.get("PORT")  # Needed for Heroku
REDIS_TLS_URL = os.environ.get("REDIS_TLS_URL")  # Set automatically in Heroku
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_DEV_CHAT_ID = os.environ.get("TELEGRAM_DEV_CHAT_ID")
TELEGRAM_WG_CHAT_ID = (
    os.environ.get("TELEGRAM_WG_CHAT_ID") if not LOCAL else TELEGRAM_DEV_CHAT_ID
)
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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_random_greeting():
    return random.choice(GREETING_LIST)


def build_message(body):
    return "\n".join([get_random_greeting(), body])


class Chatbot:
    def __init__(self):
        # Connect to Redis
        url = urlparse(REDIS_TLS_URL)
        self.r = redis.Redis(
            host=url.hostname,
            port=url.port,
            username=url.username,
            password=url.password,
            ssl=True,
            ssl_cert_reqs=None,
        )

        self.application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

        # Handlers
        self.application.add_handler(CommandHandler("meme", self.meme))
        self.application.add_handler(CommandHandler("identify", self.identify))
        self.application.add_handler(MessageHandler(filters.COMMAND, self.unknown))

        self.check_new_deployment()
        cron = self.application.job_queue
        self.add_jobs(cron)
        logger.info("Bot Started")

        try:
            self.application.run_polling(drop_pending_updates=True)
        except CancelledError:
            pass

    def meme(self, update: Update, context: CallbackContext):
        response = build_message(f"Coming soon")
        self.send_message(update.effective_chat.id, response)

    def identify(self, update: Update, context: CallbackContext):
        incoming_chat_id = update.effective_chat.id
        response = build_message(f"This chat ID: {incoming_chat_id}")
        self.send_message(update.effective_chat.id, response)

    def unknown(self, update: Update, context: CallbackContext.DEFAULT_TYPE):
        response = build_message(f"Available commands are: /meme, /identify")
        self.send_message(update.effective_chat.id, response)

    def add_jobs(self, cron):
        tz = pytz.timezone("Europe/Zurich")

        # Trash
        # Every Wednesday, Sunday at 21:00
        cron.run_daily(
            self.message_send_reminder_trash,
            days=[2, 6],
            time=datetime.time(hour=20, minute=45, second=00, tzinfo=tz),
        )
        # Paper
        # Every 2 weeks at 20:30
        cron.run_repeating(
            self.message_send_reminder_paper,
            interval=datetime.timedelta(weeks=2),
            first=datetime.datetime(2021, 10, 12, 20, 30, tzinfo=tz),
        )
        # Recycling
        # Sämi wants it every Thursday at 11
        cron.run_daily(
            self.message_send_reminder_recycling,
            days=[3],
            time=datetime.time(hour=11, minute=00, second=00, tzinfo=tz),
        )
        # Finances
        # Ryan wants it every month on the 7th at 17:00
        cron.run_monthly(
            self.message_send_reminder_finances,
            when=datetime.time(hour=17, tzinfo=tz),
            day=7,
        )

    def message_send_reminder_trash(self, context):
        message = build_message("Morn isch Mülltag.")
        self.send_wg_message(message)

    def message_send_reminder_paper(self, context):
        message = build_message("Morn isch Karton-Recycling Tag.")
        self.send_wg_message(message)

    def message_send_reminder_recycling(self, context):
        message = build_message("Bitte denk an das Recycling.")
        self.send_wg_message(message)

    def message_send_reminder_finances(self, context):
        message = build_message(
            "Ryan sollte die Finanzen regeln. Überprüfe Splitwise auf ausstehende Beträge.",
        )
        self.send_wg_message(message)

    def send_dev_message(self, message):
        """
        Sends a message to the Dev Chat
        """
        self.send_message(TELEGRAM_DEV_CHAT_ID, message)

    def send_wg_message(self, message):
        """
        Sends a message to the WG Chat
        """
        self.send_message(TELEGRAM_WG_CHAT_ID, message)

    async def send_message(self, chat_id, message):
        """
        General wrapper so code isn't littered with async/await
        """
        logger.info("Sending message to %s: %s", chat_id, message)
        await self.application.updater.bot.send_message(chat_id=chat_id, text=message)

    def check_new_deployment(self):
        """
        Because Heroku restarts dynos, we check if this is a new SHA.
        """
        last_sha_key = "last_sha"
        last_sha_val = self.r.get(last_sha_key).decode("utf-8")
        logger.info("Current SHA: %s", GITHUB_COMMIT_SHA)
        logger.info("Last SHA: %s", last_sha_val)
        if GITHUB_COMMIT_SHA != last_sha_val:
            self.send_dev_message(
                f"New Deployment\n SHA: {GITHUB_COMMIT_SHA}\n Message: {GITHUB_COMMIT_MESSAGE}"
            )
            self.r.set(last_sha_key, GITHUB_COMMIT_SHA)


if __name__ == "__main__":
    Chatbot()
