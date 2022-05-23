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
- `TELEGRAM_DEV_CHAT_ID`: The dev/test chat ID
  - note this is still included in the Github "production" environment
  - this is simply just another chat for testing commands and not spamming WG chat members
- `TELEGRAM_WG_CHAT_ID`: The actual "production" chat ID
- `IMGFLIP_USERNAME`: Used for memes, currently Ryan owns the account
- `IMGFLIP_PASSWORD`: Used for memes, currently Ryan owns the account

### Redis
Why include a redis server? Heroku periodically restarts apps, which means if we want to monitor new deployments and notify the dev channel "Hey there's a new deployment", we have to somehow maintain state to say new ≠ old.  
We store the old Github commit SHA in Redis so when the server starts up, it checks if the environment variable `GITHUB_COMMIT_SHA` is equal to what is stored in Redis.  
If not, we notify that a new deployment has taken place.  
If so, we know Heroku has restarted the dyno and it's not a new deployment.

Instead of using Redis, we could probably call Heroku API to unset a config var, but updating config vars in Heroku restarts the dyno, which gets tricky.


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

Turn off the bot on Heroku [Telegram doesn't allow multiple instances](https://dashboard.heroku.com/apps/heroku-wg-chatbot/resources)  
Click the edit icon, toggle the switch, save

### Running locally via CLI
```
LOCAL=TRUE python3 main.py
```

### Running locally via Docker
```bash
docker build -t wg_chatbot .
docker run -p8080:8080 --name wg_chatbot --env-file .env wg_chatbot
```
Check browser: localhost:8080
