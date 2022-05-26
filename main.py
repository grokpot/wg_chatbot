import asyncio
import datetime
from locale import CHAR_MAX
import logging
import os
import pytz
import random
import requests
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
IMGFLIP_USERNAME = os.environ.get("IMGFLIP_USERNAME")
IMGFLIP_PASSWORD = os.environ.get("IMGFLIP_PASSWORD")

# ENUMs
IMGFLIP_GET_MEMES_URL = "https://api.imgflip.com/get_memes"
IMGFLIP_CAPTION_MEME_URL = "https://api.imgflip.com/caption_image"
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
    loaded_memes = []

    def __init__(self):
        # Connect to Redis
        url = urlparse(REDIS_TLS_URL)
        self.redis = redis.Redis(
            host=url.hostname,
            port=url.port,
            username=url.username,
            password=url.password,
            ssl=True,
            ssl_cert_reqs=None,
        )

        self.application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

        logger.info("Bot Starting")
        self.check_new_deployment()
        self.get_memes()
        # Handlers
        self.application.add_handler(CommandHandler("identify", self.identify))
        self.application.add_handler(CommandHandler("meme", self.meme))
        self.application.add_handler(MessageHandler(filters.COMMAND, self.unknown))
        self.application.add_handler(
            MessageHandler(filters.TEXT & (~filters.COMMAND), self.random_meme)
        )
        self.add_jobs(self.application.job_queue)

    def poll(self):
        """
        Poll for user input
        """
        self.application.run_polling(drop_pending_updates=True)

    async def identify(self, update: Update, context: CallbackContext):
        """
        Helper command to get group chat ID
        """
        response = build_message(f"This chat ID: {update.effective_chat.id}")
        await self.send_message(update.effective_chat.id, response)

    async def meme(self, update: Update, context: CallbackContext.DEFAULT_TYPE):
        """
        Applies text following command to a randomly selected meme
        """
        user_text = update.message.text.replace("/meme", "")
        if not user_text:
            bot_response = (
                "Write some text after the /meme command and I'll turn it into a meme"
            )
        else:
            bot_response = self._build_meme(user_text)
        await self.send_message(update.effective_chat.id, bot_response)

    async def unknown(self, update: Update, context: CallbackContext.DEFAULT_TYPE):
        """
        Handles unknown command entry. Example: `/fake`
        """
        response = build_message(f"Available commands are: /meme, /identify")
        await self.send_message(update.effective_chat.id, response)

    async def random_meme(self, update: Update, context: CallbackContext):
        """
        Reads non-command messages and according to a set of rules, parses the message and sends a random meme
        Reading non-command messages requires group privacy to be OFF
        """
        CHAR_MIN = 5
        CHAR_MAX = 70
        RANDOM_FREQUENCY = 0.1

        # Determine if meme will be built
        message = update.message.text
        random_frequency_hit = random.random() < RANDOM_FREQUENCY
        if not (
            IMGFLIP_USERNAME
            and IMGFLIP_PASSWORD
            and CHAR_MIN < len(message) < CHAR_MAX
            and random_frequency_hit
        ):
            return

        meme_url = self._build_meme(message)
        await self.send_message(update.effective_chat.id, meme_url)

    def _build_meme(self, message: str):
        logger.info("Building Meme")
        meme = random.choice(self.loaded_memes)
        data = {
            "username": IMGFLIP_USERNAME,
            "password": IMGFLIP_PASSWORD,
            "template_id": meme["id"],
        }
        # Split the message into multiple lines depending on `box_count`
        if meme["box_count"] == 1:
            data["text1"] = message
        else:
            tokenized = message.split(" ")
            data["text0"] = " ".join(tokenized[: int(len(tokenized) / 2)])
            data["text1"] = " ".join(tokenized[int(len(tokenized) / 2) :])
        response = requests.post(IMGFLIP_CAPTION_MEME_URL, params=data)
        if response.status_code != 200 or not response.json()["success"]:
            logger.error(f"Error building meme: {response.text}")
            return "This is embarrassing - there was an error generating the meme"
        else:
            return response.json()["data"]["url"]

    def get_memes(self):
        """
        Get the list of memes from Imgflip api
        """
        self.memes = []
        response = requests.get(
            IMGFLIP_GET_MEMES_URL,
        )
        for meme in response.json()["data"]["memes"]:
            self.loaded_memes.append(meme)
        logger.info("Memes Loaded")

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
        # Test cron message
        if LOCAL:
            cron.run_repeating(
                self.message_send_cron_test,
                interval=datetime.timedelta(seconds=60),
                first=1,  # 1 second after launch
            )

    async def message_send_reminder_trash(self, context):
        message = build_message("Morn isch Mülltag.")
        await self.send_message(TELEGRAM_WG_CHAT_ID, message)

    async def message_send_reminder_paper(self, context):
        message = build_message("Morn isch Karton-Recycling Tag.")
        await self.send_message(TELEGRAM_WG_CHAT_ID, message)

    async def message_send_reminder_recycling(self, context):
        message = build_message("Bitte denk an das Recycling.")
        await self.send_message(TELEGRAM_WG_CHAT_ID, message)

    async def message_send_reminder_finances(self, context):
        message = build_message(
            "Bitte denk an die Finanzen.",
        )
        await self.send_message(TELEGRAM_WG_CHAT_ID, message)

    async def message_send_cron_test(self, context):
        message = build_message(
            "This is a cron job test.",
        )
        await self.send_message(TELEGRAM_WG_CHAT_ID, message)

    async def send_message(self, chat_id, message):
        """
        Sends a message to a chat
        """
        await self.application.updater.bot.send_message(chat_id=chat_id, text=message)

    def check_new_deployment(self):
        """
        See Readme about why we use Redis.
        """
        if self.redis.connection is None:
            logger.warning("Redis not detected. Bypassing deployment check.")
            return
        last_sha_key = "last_sha"
        last_sha_val = self.redis.get(last_sha_key).decode("utf-8")
        logger.info("Current SHA: %s", GITHUB_COMMIT_SHA)
        logger.info("Last SHA: %s", last_sha_val)
        if GITHUB_COMMIT_SHA != last_sha_val:
            func = lambda: self.send_message(
                TELEGRAM_DEV_CHAT_ID,
                f"New Deployment\n SHA: {GITHUB_COMMIT_SHA}\n Message: {GITHUB_COMMIT_MESSAGE}",
            )
            loop = asyncio.get_event_loop()
            loop.run_until_complete(func())

            self.redis.set(last_sha_key, GITHUB_COMMIT_SHA)


def main():
    bot = Chatbot()
    bot.poll()


if __name__ == "__main__":
    main()
