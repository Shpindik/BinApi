import pytest
from channels.testing import WebsocketCommunicator
from django.utils import timezone

from binance_ws.asgi import application


@pytest.mark.asyncio
@pytest.mark.django_db
class TestTickerConsumer:
    """Тесты для WebSocket"""
    async def test_connect(self):
        '''Тест подключения к WebSocket'''
        communicator = WebsocketCommunicator(application, '/ws/tickers/')
        connected, _ = await communicator.connect()
        assert connected
        await communicator.disconnect()

    async def test_receive_ticker(self):
        '''Тест получения обновлений тикеров'''
        communicator = WebsocketCommunicator(application, '/ws/tickers/')
        connected, _ = await communicator.connect()
        assert connected

        ticker_data = {
            'symbol': 'BTCUSDT',
            'price': '50000.00',
            'event_time': timezone.now().isoformat()
        }

        # Отправка данных тикера через слой каналов
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            'tickers',
            {
                'type': 'send_ticker',
                'data': ticker_data
            }
        )

        # Получение сообщения
        response = await communicator.receive_json_from()
        assert response == ticker_data

        await communicator.disconnect()

    async def test_multiple_connections(self):
        '''Тест получения обновлений тикеров через несколько подключений
        WebSocket'''
        # Создание двух подключений
        communicator1 = WebsocketCommunicator(application, '/ws/tickers/')
        communicator2 = WebsocketCommunicator(application, '/ws/tickers/')

        connected1, _ = await communicator1.connect()
        connected2, _ = await communicator2.connect()
        assert connected1 and connected2

        # Мок данных тикера
        ticker_data = {
            'symbol': 'ETHUSDT',
            'price': '3000.00',
            'event_time': timezone.now().isoformat()
        }

        # Отправка данных тикера через слой каналов
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            'tickers',
            {
                'type': 'send_ticker',
                'data': ticker_data
            }
        )

        # Оба подключения должны получить сообщение
        response1 = await communicator1.receive_json_from()
        response2 = await communicator2.receive_json_from()
        assert response1 == ticker_data
        assert response2 == ticker_data

        await communicator1.disconnect()
        await communicator2.disconnect()
