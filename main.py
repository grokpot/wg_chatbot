import logging
import time
import date
import datetime

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_NAME = 'sennwgbot'
TELEGRAM_TOKEN = '2067605659:AAGpRA95XQOzSXQtbc0bMMeoP_jiBLOq8d4'

# https://www.bern.ch/themen/abfall/entsorgungskalender/downloads/entsorgungskalender-2021-web-barroierefrei.pdf/download
PAPER_COLLECTION_DATES = (
    date.fromisoformat('2021-10-13'),
    date.fromisoformat('2021-10-27'),
    date.fromisoformat('2021-11-10'),
    date.fromisoformat('2021-11-24'),
    date.fromisoformat('2021-12-08'),
    date.fromisoformat('2021-12-22')
)


class GracefulKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self, *args):
    self.kill_now = True


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)

def notify_in_chat():
    """This method should get called once a day. Depedending on the date
       it should send a notification to bring out paper/trash
    """
    pass

def main_chatbot() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TELEGRAM_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    tasked_was_run = False
    killer = GracefulKiller()
    while not killer.kill_now:
        time.sleep(1)
        now = datetime.datetime.now()
        if now.hour == 20 and now.minute == 0 and not task_was_run:
            task_was_run = True
            notify_in_chat()
        if now.hour == 20 and now.minute == 1:
            task_was_run = False

if __name__ == '__main__':
    main_chatbot()

