FROM python:3-alpine

EXPOSE 5000

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD [ "python", "./main.py" ]
