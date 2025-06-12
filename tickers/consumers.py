import json
from channels.generic.websocket import AsyncWebsocketConsumer


class TickerConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer для обновлений тикеров.
    Подключается к группе 'tickers' и отправляет обновления тикеров
    всем подключенным клиентам.
    """
    async def connect(self):
        """Подключение к WebSocket"""
        await self.channel_layer.group_add("tickers", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """Отключение от WebSocket"""
        await self.channel_layer.group_discard("tickers", self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        pass

    async def send_ticker(self, event):
        """Отправка данных тикера в WebSocket"""
        await self.send(text_data=json.dumps(event['data']))
