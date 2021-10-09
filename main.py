import datetime
import http
import logging
import os
import pytz
import random

from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
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
"""

# ENV Vars
PORT = os.environ.get("PORT")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

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

app = Flask(__name__)

@app.route("/", methods=["GET"])
def healthcheck():
    """ Respond to Cloud Run Healthcheck """
    return "", http.HTTPStatus.NO_CONTENT

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
    current_chat_id = None

    def __init__(self):
        updater = Updater(token=TELEGRAM_BOT_TOKEN)
        dispatcher = updater.dispatcher
        dispatcher.add_handler(
            MessageHandler(Filters.text & ~Filters.command, self.message_receive)
        )
        cron = updater.job_queue

        # For testing
        # cron.run_once(self.message_send_initial_greeting, when=5)
        # cron.run_repeating(self.message_send_reminder_trash, interval=10, first=1)

        # Trash
        cron.run_daily(
            self.message_send_reminder_trash,
            days=[3, 6],
            time=datetime.time(
                hour=21, minute=00, second=00, tzinfo=pytz.timezone("Europe/Zurich")
            ),
        )
        # # Paper
        # cron.run_repeating(self.reminder_paper, interval=60, first=1)
        # # Finances
        # cron.run_repeating(self.reminder_finances, interval=60, first=1)
        # # Recycling
        # cron.run_repeating(self.reminder_recyling, interval=60, first=1)

        logger.info("Sennbot Started")
        updater.start_polling(drop_pending_updates=True)
        updater.idle()

    def message_receive(self, update: Update, context: CallbackContext) -> None:
        """
        Instead of having to ask the bot for the user/group ID and then writing it to an ENV var and restarting the bot, this checks the ID from every message and reassigns the bot if the ID changes. We have a very ADHD bot.
        """

        # Only execute when messages begin with "bot"
        if update.message.text[:3] != "bot":
            return

        incoming_chat_id = update.effective_chat.id

        # Reassign bot to new chat ID
        if incoming_chat_id != self.current_chat_id:
            self.current_chat_id = incoming_chat_id
            message = build_message(
                f"New chat ID detected. Now I'm all yours!\n ID: {self.current_chat_id}",
                self.signature,
            )
            context.bot.send_message(chat_id=self.current_chat_id, text=message)
        # Normal message parsing
        else:
            echo(update, context)

    def message_send_initial_greeting(self, context):
        message = build_message("I am online!", self.signature)
        self.send_message(context, message)

    def message_send_reminder_trash(self, context):
        message = build_message("Morn isch Mülltag", self.signature)
        self.send_message(context, message)

    def send_message(self, context, message):
        """
        Only sends a message if a current_chat_id is stored
        """
        if self.current_chat_id:
            context.bot.send_message(chat_id=self.current_chat_id, text=message)


if __name__ == "__main__":
    app.run(host="localhost", port=PORT, debug=True)
    Sennbot()
