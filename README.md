# SennWG Chatbot

To help us remind to move our lazy asses.

## Local development
```
# Create venv for pip
python3 -m venv venv
# Activate venv
source venv/bin/activate
# Install reqs
pip install -r requirements.txt

# Install pre-commit (you only need to do this once)
pre-commit install
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
