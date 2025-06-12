from rest_framework import serializers
from .models import TickerPrice


class TickerPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TickerPrice
        fields = ['id', 'symbol', 'price', 'event_time', 'received_at']
