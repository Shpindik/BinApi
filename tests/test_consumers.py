import json
import pytest
from channels.testing import WebsocketCommunicator
from django.utils import timezone

from binance_ws.asgi import application
from tickers.consumers import TickerConsumer


@pytest.mark.asyncio
@pytest.mark.django_db
class TestTickerConsumer:
    async def test_connect(self):
        """Test WebSocket connection"""
        communicator = WebsocketCommunicator(application, "/ws/tickers/")
        connected, _ = await communicator.connect()
        assert connected
        await communicator.disconnect()

    async def test_receive_ticker(self):
        """Test receiving ticker updates"""
        communicator = WebsocketCommunicator(application, "/ws/tickers/")
        connected, _ = await communicator.connect()
        assert connected

        # Mock ticker data
        ticker_data = {
            'symbol': 'BTCUSDT',
            'price': '50000.00',
            'event_time': timezone.now().isoformat()
        }

        # Send ticker data through channel layer
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            'tickers',
            {
                'type': 'send_ticker',
                'data': ticker_data
            }
        )

        # Receive the message
        response = await communicator.receive_json_from()
        assert response == ticker_data

        await communicator.disconnect()

    async def test_multiple_connections(self):
        """Test multiple WebSocket connections receiving updates"""
        # Create two connections
        communicator1 = WebsocketCommunicator(application, "/ws/tickers/")
        communicator2 = WebsocketCommunicator(application, "/ws/tickers/")
        
        connected1, _ = await communicator1.connect()
        connected2, _ = await communicator2.connect()
        assert connected1 and connected2

        # Mock ticker data
        ticker_data = {
            'symbol': 'ETHUSDT',
            'price': '3000.00',
            'event_time': timezone.now().isoformat()
        }

        # Send ticker data through channel layer
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            'tickers',
            {
                'type': 'send_ticker',
                'data': ticker_data
            }
        )

        # Both connections should receive the message
        response1 = await communicator1.receive_json_from()
        response2 = await communicator2.receive_json_from()
        assert response1 == ticker_data
        assert response2 == ticker_data

        await communicator1.disconnect()
        await communicator2.disconnect() 