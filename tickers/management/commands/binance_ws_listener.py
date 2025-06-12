import asyncio
import json
from datetime import datetime, timezone

import websockets
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from django.core.management.base import BaseCommand

from tickers.models import TickerPrice

BINANCE_WS_URL = "wss://stream.binance.com:9443/stream"
DEFAULT_SYMBOLS = ["btcusdt", "ethusdt"]


class Command(BaseCommand):
    help = "Слушает Binance WebSocket и сохраняет цены в БД"

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbols',
            nargs='+',
            default=DEFAULT_SYMBOLS,
            help='Список символов для подписки (например, btcusdt ethusdt)'
        )

    def handle(self, *args, **options):
        symbols = options['symbols']
        asyncio.run(self.listen(symbols))

    async def listen(self, symbols):
        """Listen to WebSocket stream, update DB every minute"""
        streams = [f"{symbol.lower()}@ticker" for symbol in symbols]
        stream_url = (
            f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"
        )
        last_prices = {}  # symbol -> (price, event_time)
        last_save = datetime.now(timezone.utc)
        save_interval = 60  # seconds

        async def save_all():
            for symbol, (price, event_time) in last_prices.items():
                # Delete old records for this symbol
                await sync_to_async(
                    TickerPrice.objects.filter(symbol=symbol).delete
                )()
                # Create new ticker price
                await sync_to_async(TickerPrice.objects.create)(
                    symbol=symbol,
                    price=price,
                    event_time=event_time
                )
                # Send update to WebSocket
                channel_layer = get_channel_layer()
                await channel_layer.group_send(
                    'tickers',
                    {
                        'type': 'send_ticker',
                        'data': {
                            'symbol': symbol,
                            'price': price,
                            'event_time': event_time.isoformat(),
                        }
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated {symbol}: {price} @ {event_time}'
                    )
                )

        while True:
            try:
                async with websockets.connect(stream_url) as websocket:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Connected to {stream_url}'
                        )
                    )
                    while True:
                        message = await websocket.recv()
                        symbol, price, event_time = await self.extract_ticker(
                            message
                        )
                        if symbol and price and event_time:
                            last_prices[symbol] = (price, event_time)
                        now = datetime.now(timezone.utc)
                        if (now - last_save).total_seconds() >= save_interval:
                            await save_all()
                            last_save = now
            except websockets.exceptions.ConnectionClosed:
                self.stdout.write(
                    self.style.WARNING(
                        'Connection closed. Reconnecting...'
                    )
                )
                await asyncio.sleep(5)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error: {str(e)}')
                )
                await asyncio.sleep(5)

    async def extract_ticker(self, message):
        """
        Извлекает symbol, price, event_time из сообщения.
        Возвращает (symbol, price, event_time)
        """
        try:
            data = json.loads(message)
            if 'data' not in data:
                return None, None, None
            ticker_data = data['data']
            symbol = ticker_data.get('s')
            price = ticker_data.get('c')
            event_time_ms = ticker_data.get('E')
            if not symbol or not price or not event_time_ms:
                return None, None, None
            event_time = datetime.fromtimestamp(
                int(event_time_ms) / 1000, tz=timezone.utc
            )
            return symbol, price, event_time
        except Exception:
            return None, None, None
