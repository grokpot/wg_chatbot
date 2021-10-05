# SennWG Chatbot

To help us remind to move our lazy asses.

## Build Docker image
```bash
docker build -t wg_chatbot .
```

## Run Docker image
```bash
docker run -p5000:5000 wg_chatbot
```

Check browser: localhost:5000

Flask/Webserver may be removed once chatbot is actually running.
