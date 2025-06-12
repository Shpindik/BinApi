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
                'p': '50000.00',
                'T': int(timezone.now().timestamp() * 1000)
            }
        })

        # Process the message
        await command.process_message(message)

        # Check if ticker was created in database
        ticker = await self.get_ticker()
        assert ticker is not None
        assert ticker.symbol == 'BTCUSDT'
        assert Decimal(ticker.price) == Decimal('50000.00')

    async def test_listen_multiple_symbols(self, command, mock_websocket):
        """Test listening to multiple symbols"""
        symbols = ['btcusdt', 'ethusdt']
        
        # Mock WebSocket messages
        mock_ws = mock_websocket.return_value.__aenter__.return_value
        mock_ws.__aiter__.return_value = [
            json.dumps({
                'data': {
                    's': 'BTCUSDT',
                    'p': '50000.00',
                    'T': int(timezone.now().timestamp() * 1000)
                }
            }),
            json.dumps({
                'data': {
                    's': 'ETHUSDT',
                    'p': '3000.00',
                    'T': int(timezone.now().timestamp() * 1000)
                }
            })
        ]

        # Start listening
        await command.listen(symbols)

        # Check if both tickers were created
        tickers = await self.get_tickers()
        assert len(tickers) == 2
        symbols = {t.symbol for t in tickers}
        assert 'BTCUSDT' in symbols
        assert 'ETHUSDT' in symbols

    async def test_invalid_message(self, command, mock_websocket):
        """Test handling invalid message format"""
        # Mock invalid message
        message = json.dumps({'invalid': 'format'})

        # Process the message
        await command.process_message(message)

        # No ticker should be created
        count = await self.get_ticker_count()
        assert count == 0 