import json
import pytest
from unittest.mock import AsyncMock, patch
from django.utils import timezone
from asgiref.sync import sync_to_async
from decimal import Decimal
from django.db import transaction

from tickers.management.commands.binance_ws_listener import Command
from tickers.models import TickerPrice


@pytest.mark.django_db(transaction=True)
class TestBinanceListener:
    """
    Тесты для команды прослушивания Binance WebSocket и сохранения цен тикеров
    в БД
    """
    @pytest.fixture(autouse=True)
    def setup_method(self):
        '''Очищает базу данных перед каждым тестом'''
        with transaction.atomic():
            TickerPrice.objects.all().delete()

    @pytest.fixture
    def command(self):
        '''Возвращает экземпляр команды для тестирования'''
        return Command()

    @pytest.fixture
    def mock_websocket(self):
        '''Мок WebSocket для тестирования'''
        with patch('websockets.connect') as mock:
            mock.return_value.__aenter__.return_value = AsyncMock()
            yield mock

    @sync_to_async
    def get_ticker(self):
        '''Возвращает первый тикер из базы данных'''
        with transaction.atomic():
            return TickerPrice.objects.first()

    @sync_to_async
    def get_tickers(self):
        '''Возвращает список всех тикеров из базы данных'''
        with transaction.atomic():
            return list(TickerPrice.objects.all())

    @sync_to_async
    def get_ticker_count(self):
        '''Возвращает количество тикеров в базе данных'''
        with transaction.atomic():
            return TickerPrice.objects.count()

    async def test_process_message(self, command, mock_websocket):
        '''Тест обработки сообщения из Binance WebSocket'''
        # Мок сообщения из Binance
        message = json.dumps({
            'data': {
                's': 'BTCUSDT',
                'c': '50000.00',
                'E': int(timezone.now().timestamp() * 1000)
            }
        })

        # Извлечение данных тикера
        symbol, price, event_time = await command.extract_ticker(message)

        # Проверка извлеченных данных
        assert symbol == 'BTCUSDT'
        assert Decimal(price) == Decimal('50000.00')
        assert event_time is not None

    async def test_invalid_message(self, command, mock_websocket):
        '''Тест обработки сообщения с неверным форматом'''
        # Мок неверного сообщения
        message = json.dumps({'invalid': 'format'})

        # Извлечение данных тикера
        symbol, price, event_time = await command.extract_ticker(message)

        # Проверка извлеченных данных
        assert symbol is None
        assert price is None
        assert event_time is None
