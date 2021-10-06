FROM python:3-alpine

RUN apk update && apk add --no-cache build-base

WORKDIR /app

ADD requirements /app/requirements
RUN pip install --no-cache-dir -r requirements/prod-top.txt

COPY main.py .

CMD [ "python", "./main.py" ]
