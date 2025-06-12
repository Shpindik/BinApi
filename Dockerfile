FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p static staticfiles templates

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "binance_ws.asgi:application"]
