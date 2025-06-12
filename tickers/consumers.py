import json
from channels.generic.websocket import AsyncWebsocketConsumer


class TickerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Connect to WebSocket"""
        await self.channel_layer.group_add("tickers", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """Disconnect from WebSocket"""
        await self.channel_layer.group_discard("tickers", self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        pass

    async def send_ticker(self, event):
        """Send ticker data to WebSocket"""
        await self.send(text_data=json.dumps(event['data']))
