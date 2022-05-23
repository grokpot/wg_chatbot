FROM python:3.10-alpine

RUN apk update && apk add --no-cache build-base

WORKDIR /app

ENV PORT 8080
EXPOSE ${PORT}

ADD requirements /app/requirements
RUN pip install -r requirements/prod-top.txt

COPY main.py .

CMD [ "python", "./main.py" ]
