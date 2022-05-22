# SennWG Chatbot

To help us remind to move our lazy asses.

## Architecture
The bot is owned by one person and runs on Heroku.  
Heroku access can be granted via email.  
Environment variables are set in GITHUB as *environment secrets* and transferred to Heroku.   
This means:
```diff
- only make changes to Github secrets, Heroku config vars are overwritten on commit!
```

When code is updated, a Github Action runs and deploys the updated code to Heroku.

The following env vars are required in Github under the `production` environment:
- `HEROKU_API_KEY`: The account-associated API key
- `HEROKU_RYANS_EMAIL`: The account email address
- `TELEGRAM_BOT_TOKEN`: The bot API token (see `Bot Setup`)
- `TELEGRAM_DEV_CHAT_ID`: The dev/test chat ID - note this is still included in the Github "production" environment - this is simply just another chat for testing commands and not spamming WG chat members
- `TELEGRAM_WG_CHAT_ID`: The actual "production" chat ID


## Bot Setup
Telegram has a bot factory user name "BotFather". Steps to setting up a new bot:
1. Message "BotFather"
2. Type `/mybots` to check if bots already exist
3. Type `/newbot` to create a new bot and follow instructions
4. Type `/mybots`, select the new bot, and click `API Token` to generate a new token
5. Copy token into Heroku config var `TELEGRAM_BOT_TOKEN`
6. For a dev chat environment, create a group and [get the ID](https://stackoverflow.com/questions/32423837/telegram-bot-how-to-get-a-group-chat-id_), and copy it to the heroku config `TELEGRAM_DEV_CHAT_ID`
7. For a prod environment, create a group, get the ID, and copy it to the heroku config `TELEGRAM_WG_CHAT_ID`

## Local development

### Setup
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

### Running locally
Turn off the bot on Heroku (Telegram doesn't allow multiple instances)
https://dashboard.heroku.com/apps/heroku-wg-chatbot/resources
Click the edit icon, toggle the switch, save

To run:
```
LOCAL=TRUE python3 main.py
```

#### Build Docker image
```bash
docker build -t wg_chatbot .
```

#### Run Docker image
```bash
docker run -p5000:5000 --name wg_chatbot wg_chatbot
```

Check browser: localhost:5000

Flask/Webserver may be removed once chatbot is actually running.
