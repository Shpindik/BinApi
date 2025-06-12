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
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Clear database before each test"""
        with transaction.atomic():
            TickerPrice.objects.all().delete()

    @pytest.fixture
    def command(self):
        return Command()

    @pytest.fixture
    def mock_websocket(self):
        with patch('websockets.connect') as mock:
            mock.return_value.__aenter__.return_value = AsyncMock()
            yield mock

    @sync_to_async
    def get_ticker(self):
        with transaction.atomic():
            return TickerPrice.objects.first()

    @sync_to_async
    def get_tickers(self):
        with transaction.atomic():
            return list(TickerPrice.objects.all())

    @sync_to_async
    def get_ticker_count(self):
        with transaction.atomic():
            return TickerPrice.objects.count()

    async def test_process_message(self, command, mock_websocket):
        """Test processing a message from Binance WebSocket"""
        # Mock message from Binance
        message = json.dumps({
            'data': {
                's': 'BTCUSDT',
                'c': '50000.00',
                'E': int(timezone.now().timestamp() * 1000)
            }
        })

        # Extract ticker data
        symbol, price, event_time = await command.extract_ticker(message)

        # Check extracted data
        assert symbol == 'BTCUSDT'
        assert Decimal(price) == Decimal('50000.00')
        assert event_time is not None

    async def test_invalid_message(self, command, mock_websocket):
        """Test handling invalid message format"""
        # Mock invalid message
        message = json.dumps({'invalid': 'format'})

        # Extract ticker data
        symbol, price, event_time = await command.extract_ticker(message)

        # Check extracted data
        assert symbol is None
        assert price is None
        assert event_time is None