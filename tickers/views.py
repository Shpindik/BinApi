from django.utils.dateparse import parse_datetime
from django.db.models import Max
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import TickerPrice
from .serializers import TickerPriceSerializer


class TickerPriceListView(generics.ListAPIView):
    serializer_class = TickerPriceSerializer

    def get_queryset(self):
        """
        Возвращает последний тикер для каждого символа.
        Если указан символ, возвращает только последний тикер
        для этого символа.
        """
        symbol = self.request.query_params.get('symbol')
        subquery = TickerPrice.objects.values('symbol').annotate(
            latest_event_time=Max('event_time')
        )
        queryset = TickerPrice.objects.filter(
            event_time__in=[entry['latest_event_time'] for entry in subquery]
        )
        if symbol:
            latest_event_time = TickerPrice.objects.filter(
                symbol__iexact=symbol
            ).aggregate(
                latest_event_time=Max('event_time')
            )['latest_event_time']
            queryset = queryset.filter(event_time=latest_event_time)
        return queryset.order_by('-event_time')


class TickerPriceHistoryView(APIView):
    """Просмотр истории цен через REST API"""
    def get(self, request):
        """
        Возвращает историю цен с возможностью фильтрации
        по символу и диапазону времени.
        """
        symbol = request.query_params.get('symbol')
        start = request.query_params.get('start')
        end = request.query_params.get('end')

        queryset = TickerPrice.objects.all()
        if symbol:
            queryset = queryset.filter(symbol__iexact=symbol)
        if start:
            dt_start = parse_datetime(start)
            if dt_start:
                queryset = queryset.filter(event_time__gte=dt_start)
        if end:
            dt_end = parse_datetime(end)
            if dt_end:
                queryset = queryset.filter(event_time__lte=dt_end)

        data = list(
            queryset.order_by('-event_time').values(
                'id', 'symbol', 'price', 'event_time'
            )
        )
        return Response(data)
