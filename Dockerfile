FROM python:3.8-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN python indexerOK.py

ENV PORT=8080

EXPOSE 8080

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 server:app