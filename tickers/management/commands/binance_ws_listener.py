import asyncio
import json
from datetime import datetime, timezone

import websockets
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from django.core.management.base import BaseCommand

from tickers.models import TickerPrice

BINANCE_WS_URL = 'wss://stream.binance.com:9443/stream'
DEFAULT_SYMBOLS = ['btcusdt', 'ethusdt']


class Command(BaseCommand):
    """
    Слушает Binance WebSocket и сохраняет цены в БД
    """

    help = 'Слушает Binance WebSocket и сохраняет цены в БД'

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
        """Слушает поток WebSocket, обновляет БД каждую минуту"""
        streams = [f"{symbol.lower()}@ticker" for symbol in symbols]
        stream_url = (
            f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"
        )
        last_prices = {}  # symbol -> (price, event_time)
        last_save = datetime.now(timezone.utc)
        save_interval = 60  # seconds

        async def save_all():
            for symbol, (price, event_time) in last_prices.items():
                # Создание новой записи цены тикера без удаления старых записей
                await sync_to_async(TickerPrice.objects.create)(
                    symbol=symbol,
                    price=price,
                    event_time=event_time
                )
                # Отправка обновления в WebSocket
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
                        f'Обновлено {symbol}: {float(price):.1f} @ '
                        f'{event_time.strftime("%Y-%m-%d %H:%M:%S UTC")}'
                    )
                )

        while True:
            try:
                async with websockets.connect(stream_url) as websocket:
                    formatted_time = datetime.now(timezone.utc).strftime(
                        "%Y-%m-%d %H:%M:%S UTC"
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Подключено к {stream_url} в {formatted_time}'
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
                formatted_time = datetime.now(timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S UTC"
                )
                self.stdout.write(
                    self.style.WARNING(
                        f'Соединение закрыто в {formatted_time}. '
                        'Переподключение...'
                    )
                )
                await asyncio.sleep(5)
            except Exception as e:
                formatted_time = datetime.now(timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S UTC"
                )
                self.stdout.write(
                    self.style.ERROR(
                        f'Ошибка в {formatted_time}: {str(e)}'
                    )
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
