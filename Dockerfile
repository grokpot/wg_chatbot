FROM python:3-alpine

EXPOSE 5000

WORKDIR /app

ADD requirements /app/requirements
RUN pip install --no-cache-dir -r requirements/prod-top.txt

COPY main.py .

CMD [ "python", "./main.py" ]
