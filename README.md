# SennWG Chatbot

To help us remind to move our lazy asses.

## Local development setup
```
# Create venv for pip
python3 -m venv venv
# Activate venv
source venv/bin/activate
# Install reqs
pip install -r requirements/dev-top.txt

# Install pre-commit (you only need to do this once)
pre-commit install

Add a `.env` file to your directory with the following keys and values:
TELEGRAM_BOT_TOKEN=VALUE
TELEGRAM_DEV_CHAT_ID=VALUE
TELEGRAM_WG_CHAT_ID=VALUE
REDIS_TLS_URL=VALUE
```

## Running locally
Turn off the bot on Heroku (Telegram doesn't allow multiple instances)
https://dashboard.heroku.com/apps/heroku-wg-chatbot/resources
Click the edit icon, toggle the switch, save

To run:
```
LOCAL=TRUE python3 main.py
```

## Build Docker image
```bash
docker build -t wg_chatbot .
```

## Run Docker image
```bash
docker run -p5000:5000 --name wg_chatbot wg_chatbot
```

Check browser: localhost:5000

Flask/Webserver may be removed once chatbot is actually running.
